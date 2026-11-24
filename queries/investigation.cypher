// SENTINEL graph investigation queries
// Run these queries in Neo4j Browser after loading the graph.

// Investigation 1: Distinct customers sharing devices
// within a rolling 7-day window.

MATCH (c:Customer)-[u:USED_DEVICE]->(d:Device)

WITH
    d,
    collect({
        customer_id: c.customer_id,
        used_at: u.time
    }) AS usages

UNWIND usages AS anchor

WITH
    d,
    anchor,
    [x IN usages
     WHERE x.used_at >= anchor.used_at - duration({days: 7})
       AND x.used_at <= anchor.used_at
    ] AS window_usages

WITH
    d,
    anchor.used_at AS window_end,
    window_usages

UNWIND window_usages AS usage

WITH
    d,
    window_end,
    count(DISTINCT usage.customer_id) AS distinct_customer_count

WHERE distinct_customer_count >= 2

RETURN
    d.device_id AS device_id,
    distinct_customer_count,
    window_end - duration({days: 7}) AS window_start,
    window_end

ORDER BY distinct_customer_count DESC, device_id;

// -----------------------------------------------------------------------------
// Query 2: Two-hop fraud proximity.
// Returns customers connected to a fraud-labelled payment through either:
// (a) a shared device used by the fraud transaction, or
// (b) the same merchant that received the fraud-labelled payment.
// Each path contains two relationships from the investigated customer to the
// fraud payment's customer/merchant endpoint.
MATCH (investigated:Customer)-[:USED_DEVICE]->(shared:Device)<-[fraud_device_use:USED_DEVICE]-(fraud_customer:Customer)
MATCH (fraud_customer)-[fraud_payment:PAID]->(:Merchant)
WHERE investigated <> fraud_customer
  AND fraud_payment.fraud_label = 1
  AND fraud_payment.transaction_id = fraud_device_use.transaction_id
RETURN DISTINCT
    investigated.customer_id AS customer_id,
    fraud_customer.customer_id AS connected_fraud_customer_id,
    'SHARED_DEVICE' AS connection_type,
    shared.device_id AS shared_entity_id
UNION
MATCH (investigated:Customer)-[:PAID]->(shared:Merchant)<-[fraud_payment:PAID]-(fraud_customer:Customer)
WHERE investigated <> fraud_customer
  AND fraud_payment.fraud_label = 1
RETURN DISTINCT
    investigated.customer_id AS customer_id,
    fraud_customer.customer_id AS connected_fraud_customer_id,
    'SHARED_MERCHANT' AS connection_type,
    shared.merchant_id AS shared_entity_id;


// -----------------------------------------------------------------------------
// Query 3: Rank merchants by payments made by customers using shared devices.
// The payment is joined to the device-use relationship by transaction_id.
// -----------------------------------------------------------------------------
MATCH (c:Customer)-[u:USED_DEVICE]->(d:Device)
WITH d, count(DISTINCT c) AS distinct_customer_count
WHERE distinct_customer_count >= 2
MATCH (c:Customer)-[u:USED_DEVICE]->(d)
MATCH (c)-[p:PAID]->(m:Merchant)
WHERE p.transaction_id = u.transaction_id
WITH
    m,
    count(DISTINCT p.transaction_id) AS shared_device_payment_count,
    count(DISTINCT c.customer_id) AS distinct_customer_count,
    count(DISTINCT d.device_id) AS shared_device_count
RETURN
    m.merchant_id AS merchant_id,
    m.name AS merchant_name,
    shared_device_payment_count,
    distinct_customer_count,
    shared_device_count
ORDER BY shared_device_payment_count DESC, merchant_id
LIMIT 10;
