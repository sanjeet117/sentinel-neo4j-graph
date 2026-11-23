import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Read Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate configuration
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or key is missing from .env")

# Create Supabase client
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# Test connection by reading customers
response = (
    supabase.table("customers")
    .select("customer_id")
    .limit(5)
    .execute()
)

print("Supabase connection successful!")
print("Customers fetched:", len(response.data))
print("Sample customer IDs:")

for customer in response.data:
    print(customer["customer_id"])