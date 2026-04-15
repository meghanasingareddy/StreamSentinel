import os
import json
import time
import logging
import requests
from kafka import KafkaConsumer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("AlertingService")

# Environment Variables
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = os.getenv('TOPIC_ANOMALIES', 'anomalies')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

def send_alert(transaction):
    """
    Simulates sending an alert. 
    If SLACK_WEBHOOK_URL is provided, it makes a real HTTP request.
    """
    tx_id = transaction.get('transaction_id', 'UNKNOWN')
    amount = transaction.get('amount', 0)
    user = transaction.get('user_id', 'UNKNOWN')
    
    alert_msg = (
        f"🚨 *CRITICAL ALERT: Anomaly Detected!* 🚨\n"
        f"Transaction ID: {tx_id}\n"
        f"User ID: {user}\n"
        f"Amount: ${amount}\n"
        f"Action Required: Immediate review of account activity."
    )
    
    logger.error(f"FIRING ALERT -> {alert_msg}")
    
    if SLACK_WEBHOOK_URL:
        # In a real environment, uncomment to send to slack!
        try:
            payload = {"text": alert_msg}
            # response = requests.post(SLACK_WEBHOOK_URL, json=payload)
            # logger.info(f"Slack response: {response.status_code}")
            logger.info("Mock-sent Slack Webhook successfully (code commented out for safety).")
        except Exception as e:
            logger.error(f"Failed to trigger webhook: {e}")
    else:
        logger.info("No webhook URL configured. Alert logged locally.")

def get_kafka_consumer():
    retries = 5
    while retries > 0:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='alerting-group'
            )
            logger.info("Successfully connected to Kafka.")
            return consumer
        except Exception as e:
            logger.warning(f"Error connecting to Kafka: {e}. Retrying...")
            time.sleep(5)
            retries -= 1
            
    logger.error("Failed to connect to Kafka.")
    return None

def main():
    logger.info("Initializing Alerting System microservice...")
    consumer = get_kafka_consumer()
    
    if not consumer:
        return

    logger.info(f"Listening on topic '{TOPIC}' for anomalies...")

    try:
        for message in consumer:
            tx = message.value
            
            # Check if ML flagged this as an anomaly
            if tx.get('ml_anomaly') is True:
                send_alert(tx)
                
    except KeyboardInterrupt:
        logger.info("Stopping alerting service...")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
