
from src.supabase_connection import supabase

# Check total transaction records
response = (
    supabase.table("transactions")
    .select("transaction_id", count="exact")
    .limit(1)
    .execute()
)

print("Total transactions:", response.count)

# Fetch 5 sample transactions
transactions = (
    supabase.table("transactions")
    .select(
        "transaction_id, customer_id, merchant_id, "
        "device_id, transaction_amount, transaction_time"
    )
    .order("transaction_id")
    .limit(5)
    .execute()
)

print("\nSample transactions:")

for transaction in transactions.data:
    print(transaction)

# Check fraud labels
labels = (
    supabase.table("labels")
    .select("transaction_id, fraud_label")
    .limit(5)
    .execute()
)

print("\nSample fraud labels:")

for label in labels.data:
    print(label)
