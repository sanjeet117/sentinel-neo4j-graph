
from src.supabase_connection import supabase


def fetch_transactions(limit=5000, batch_size=1000):
    """
    Fetch transactions from Supabase using pagination.
    """

    all_transactions = []

    for start in range(0, limit, batch_size):
        end = min(start + batch_size, limit) - 1

        response = (
            supabase.table("transactions")
            .select("*")
            .order("transaction_id")
            .range(start, end)
            .execute()
        )

        batch = response.data
        all_transactions.extend(batch)

        print(
            f"Fetched {len(batch)} transactions | "
            f"Total: {len(all_transactions)}"
        )

        if not batch:
            break

    return all_transactions


def fetch_labels(transaction_ids):
    """
    Fetch fraud labels for the selected transactions.
    """

    all_labels = []

    # Supabase IN filters are split into smaller batches.
    for start in range(0, len(transaction_ids), 500):
        batch_ids = transaction_ids[start:start + 500]

        response = (
            supabase.table("labels")
            .select("transaction_id, fraud_label")
            .in_("transaction_id", batch_ids)
            .execute()
        )

        all_labels.extend(response.data)

    return all_labels


if __name__ == "__main__":

    transactions = fetch_transactions(limit=5000)

    transaction_ids = [
        transaction["transaction_id"]
        for transaction in transactions
    ]

    labels = fetch_labels(transaction_ids)

    print("\nDATA EXTRACTION SUMMARY")
    print("Transactions fetched:", len(transactions))
    print("Labels fetched:", len(labels))

    fraud_count = sum(
        1 for label in labels
        if label["fraud_label"] == 1
    )

    print("Fraud-labelled transactions:", fraud_count)
    print("Non-fraud-labelled transactions:", len(labels) - fraud_count)
