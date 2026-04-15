import json
import time
import random
import uuid
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'transactions'

def create_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        return producer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        return None

def generate_transaction():
    # Normal transaction $10 to $1000
    # Anomaly transaction $5000 to $20000
    is_anomaly = random.random() < 0.05
    amount = round(random.uniform(5000, 20000), 2) if is_anomaly else round(random.uniform(10, 1000), 2)
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": f"user_{random.randint(1, 100)}",
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat(),
        "is_synthetic_anomaly": is_anomaly  # Just for testing our ML model later
    }
    return transaction

def main():
    producer = create_producer()
    if not producer:
        print("Could not start producer.")
        return
    
    print(f"Starting data generation to topic '{TOPIC}'...")
    try:
        while True:
            tx = generate_transaction()
            producer.send(TOPIC, value=tx)
            # print(f"Sent: {tx}")
            time.sleep(random.uniform(0.1, 1.0))
    except KeyboardInterrupt:
        print("Stopping generator...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
