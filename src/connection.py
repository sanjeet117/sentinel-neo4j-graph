
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


def create_constraints():
    constraints = [
        """
        CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
        FOR (c:Customer)
        REQUIRE c.customer_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT device_id_unique IF NOT EXISTS
        FOR (d:Device)
        REQUIRE d.device_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS
        FOR (m:Merchant)
        REQUIRE m.merchant_id IS UNIQUE
        """
    ]

    with driver.session(database=DATABASE) as session:
        for query in constraints:
            session.run(query)

    print("All uniqueness constraints created successfully!")


if __name__ == "__main__":
    try:
        driver.verify_connectivity()
        create_constraints()
    finally:
        driver.close()
