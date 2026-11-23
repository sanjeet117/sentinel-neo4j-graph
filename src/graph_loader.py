
from src.connection import driver, DATABASE
from src.data_loader import fetch_transactions, fetch_labels
from src.supabase_connection import supabase


REQUIRED_TRANSACTIONS = 5000
FETCH_LIMIT = 6000


def fetch_related_records(table, id_column, ids, columns):
    records = {}

    for start in range(0, len(ids), 500):
        batch_ids = ids[start:start + 500]

        response = (
            supabase.table(table)
            .select(columns)
            .in_(id_column, batch_ids)
            .execute()
        )

        for record in response.data:
            records[record[id_column]] = record

    return records


def create_graph(transactions, labels, devices, merchants):

    label_map = {
        item["transaction_id"]: item["fraud_label"]
        for item in labels
    }

    loaded = 0

    with driver.session(database=DATABASE) as session:

        for transaction in transactions:

            customer_id = transaction["customer_id"]
            device_id = transaction["device_id"]
            merchant_id = transaction["merchant_id"]
            transaction_id = transaction["transaction_id"]

            device = devices.get(device_id, {})
            merchant = merchants.get(merchant_id, {})

            session.run(
                """
                MERGE (c:Customer {customer_id: $customer_id})
                MERGE (d:Device {device_id: $device_id})
                MERGE (m:Merchant {merchant_id: $merchant_id})

                SET d.device_kind = $device_kind,
                    m.name = $merchant_name,
                    m.merchant_category = $merchant_category

                MERGE (c)-[u:USED_DEVICE {
                    transaction_id: $transaction_id
                }]->(d)

                SET u.time = datetime($transaction_time)

                MERGE (c)-[p:PAID {
                    transaction_id: $transaction_id
                }]->(m)

                SET p.amount = $amount,
                    p.time = datetime($transaction_time),
                    p.fraud_label = $fraud_label
                """,
                customer_id=customer_id,
                device_id=device_id,
                merchant_id=merchant_id,
                device_kind=device.get("device_kind"),
                merchant_name=merchant.get("synthetic_name"),
                merchant_category=merchant.get("merchant_category"),
                transaction_id=transaction_id,
                amount=transaction["transaction_amount"],
                transaction_time=transaction["transaction_time"],
                fraud_label=label_map.get(transaction_id, 0)
            )

            loaded += 1

    print("\nGRAPH LOADING SUMMARY")
    print("Valid transactions loaded:", loaded)
    print("Fraud labels available:", len(labels))
    print("Graph loading completed!")


if __name__ == "__main__":

    try:
        # Fetch extra records to account for missing IDs
        transactions = fetch_transactions(limit=FETCH_LIMIT)

        # Keep only transactions with all required IDs
        valid_transactions = [
            item for item in transactions
            if item.get("customer_id")
            and item.get("device_id")
            and item.get("merchant_id")
        ]

        # Select exactly 5,000 valid transactions
        transactions = valid_transactions[:REQUIRED_TRANSACTIONS]

        print("Raw transactions fetched:", len(valid_transactions))
        print("Valid transactions selected:", len(transactions))

        if len(transactions) < REQUIRED_TRANSACTIONS:
            raise ValueError(
                f"Only {len(transactions)} valid transactions found. "
                f"At least {REQUIRED_TRANSACTIONS} are required."
            )

        transaction_ids = [
            item["transaction_id"] for item in transactions
        ]

        device_ids = list({
            item["device_id"] for item in transactions
        })

        merchant_ids = list({
            item["merchant_id"] for item in transactions
        })

        labels = fetch_labels(transaction_ids)

        devices = fetch_related_records(
            "devices",
            "device_id",
            device_ids,
            "device_id, device_kind"
        )

        merchants = fetch_related_records(
            "merchants",
            "merchant_id",
            merchant_ids,
            "merchant_id, synthetic_name, merchant_category"
        )

        print("Devices fetched:", len(devices))
        print("Merchants fetched:", len(merchants))
        print("Labels fetched:", len(labels))

        create_graph(
            transactions,
            labels,
            devices,
            merchants
        )

    finally:
        driver.close()
