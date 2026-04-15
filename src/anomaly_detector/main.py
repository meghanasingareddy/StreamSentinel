import os
import json
import time
import logging
from kafka import KafkaConsumer, KafkaProducer
from model import StreamingAnomalyDetector

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("AnomalyDetectorMain")

# Environment Variables
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = os.getenv('TOPIC_TRANSACTIONS', 'transactions')
OUTPUT_TOPIC = os.getenv('TOPIC_ANOMALIES', 'anomalies')

def get_kafka_components():
    retries = 5
    while retries > 0:
        try:
            consumer = KafkaConsumer(
                INPUT_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='anomaly-detector-group'
            )
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka components.")
            return consumer, producer
        except Exception as e:
            logger.warning(f"Error connecting to Kafka: {e}. Retrying...")
            time.sleep(5)
            retries -= 1
            
    logger.error("Failed to connect to Kafka components after retries.")
    return None, None

def main():
    logger.info("Initializing Anomaly Detector microservice...")
    consumer, producer = get_kafka_components()
    
    if not consumer or not producer:
        return

    detector = StreamingAnomalyDetector(
        n_estimators=100, 
        contamination=0.05, 
        window_size=100, 
        min_fit_size=50
    )

    logger.info(f"Listening on topic '{INPUT_TOPIC}', outputting to '{OUTPUT_TOPIC}'...")

    try:
        for message in consumer:
            tx = message.value
            amount = float(tx.get('amount', 0))
            
            # Predict
            is_ml_anomaly = detector.process_and_predict(amount)
            tx['ml_anomaly'] = is_ml_anomaly
            
            # Publish prediction
            producer.send(OUTPUT_TOPIC, value=tx)
            
            if is_ml_anomaly:
                logger.warning(f"🚨 ML_ANOMALY DETECTED: {tx}")
            else:
                logger.debug(f"Normal tx processed: {tx['transaction_id']}")
                
    except KeyboardInterrupt:
        logger.info("Stopping anomaly detector...")
    finally:
        consumer.close()
        producer.close()
        logger.info("Kafka components closed.")

if __name__ == "__main__":
    main()
