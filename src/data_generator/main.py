import os
import json
import time
import random
import uuid
import logging
from datetime import datetime
from kafka import KafkaProducer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("DataGenerator")

# Environment Variables
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = os.getenv('TOPIC_TRANSACTIONS', 'transactions')
DELAY = float(os.getenv('GENERATOR_DELAY', '0.5'))

def create_producer():
    logger.info(f"Connecting to Kafka at {KAFKA_BROKER}...")
    # Add a retry loop for robust startup
    retries = 5
    while retries > 0:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka.")
            return producer
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka. Retrying in 5 seconds... ({e})")
            time.sleep(5)
            retries -= 1
    
    logger.error("Could not connect to Kafka after multiple retries.")
    return None

def generate_transaction():
    """Simulates a financial transaction. ~5% chance of being artificially anomalous."""
    is_anomaly = random.random() < 0.05
    amount = round(random.uniform(5000, 20000), 2) if is_anomaly else round(random.uniform(10, 1000), 2)
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": f"user_{random.randint(1, 100)}",
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat(),
        "is_synthetic_anomaly": is_anomaly
    }
    return transaction

def main():
    logger.info("Initializing Data Generator microservice...")
    producer = create_producer()
    if not producer:
        return
    
    logger.info(f"Producing transactions to topic '{TOPIC}'. Delay={DELAY}s.")
    try:
        while True:
            tx = generate_transaction()
            producer.send(TOPIC, value=tx)
            logger.info(f"Produced transaction {tx['transaction_id']} (Amount: ${tx['amount']})")
            
            # Flush periodically or just let background thread handle it, 
            # here we sleep which gives kafka-python time
            time.sleep(DELAY)
    except KeyboardInterrupt:
        logger.info("Interrupt received. Stopping generator...")
    finally:
        producer.close()
        logger.info("Producer closed.")

if __name__ == "__main__":
    main()
