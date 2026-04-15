import json
import numpy as np
from kafka import KafkaConsumer, KafkaProducer
from sklearn.ensemble import IsolationForest

KAFKA_BROKER = 'localhost:9092'
INPUT_TOPIC = 'transactions'
OUTPUT_TOPIC = 'anomalies'

def get_kafka_components():
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
        return consumer, producer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        return None, None

def main():
    consumer, producer = get_kafka_components()
    if not consumer or not producer:
        print("Could not start Kafka components.")
        return

    print("Initializing IsolationForest model...")
    # Initialize Isolation Forest. In a real system, you'd load a pre-trained model
    # Here we learn dynamically over windows of data
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    
    # Store recent amounts to fit the model dynamically (sliding window)
    window_size = 100
    recent_data = []

    print(f"Listening on topic '{INPUT_TOPIC}'...")

    try:
        for message in consumer:
            tx = message.value
            amount = float(tx.get('amount', 0))
            
            recent_data.append([amount])
            
            if len(recent_data) > window_size:
                recent_data.pop(0)

            # Fit model and predict if we have enough data
            if len(recent_data) >= 50:
                model.fit(recent_data)
                prediction = model.predict([[amount]])[0]
                
                # -1 means anomaly, 1 means normal
                is_ml_anomaly = bool(prediction == -1)
                
                # Update transaction with ml result
                tx['ml_anomaly'] = is_ml_anomaly
                
                # Always send to anomalies topic for dashboard to show
                # Even normal ones, so the frontend can plot the stream
                producer.send(OUTPUT_TOPIC, value=tx)
                
                if is_ml_anomaly:
                    print(f"🚨 Anomaly Detected: {tx}")
    except KeyboardInterrupt:
        print("Stopping anomaly detector...")
    finally:
        consumer.close()
        producer.close()

if __name__ == "__main__":
    main()
