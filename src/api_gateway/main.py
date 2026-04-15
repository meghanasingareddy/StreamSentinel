import os
import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("APIGateway")

app = FastAPI(title="StreamSentinel API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
OUTPUT_TOPIC = os.getenv('TOPIC_ANOMALIES', 'anomalies')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")

manager = ConnectionManager()

def get_kafka_consumer():
    try:
        return KafkaConsumer(
            OUTPUT_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='websocket-broadcaster'
        )
    except Exception as e:
        logger.error(f"Error connecting to Kafka: {e}")
        return None

async def consume_to_websocket():
    # Adding a slight delay to ensure Kafka broker is ready on startup
    await asyncio.sleep(5)
    
    consumer = get_kafka_consumer()
    if not consumer:
        logger.error("Failed to start Kafka consumer in background task.")
        return
    
    logger.info("Started background task: consuming anomalies and pushing to WebSockets.")
    loop = asyncio.get_running_loop()
    try:
        while True:
            # Poll kafka for messages (non-blocking in async context via run_in_executor)
            messages = await loop.run_in_executor(None, consumer.poll, 1.0)
            for tp, msgs in messages.items():
                for msg in msgs:
                    await manager.broadcast(json.dumps(msg.value))
            await asyncio.sleep(0.05)
    except Exception as e:
        logger.error(f"Kafka consumer stream error: {e}")
    finally:
        consumer.close()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing background WebSocket broadcaster...")
    asyncio.create_task(consume_to_websocket())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
