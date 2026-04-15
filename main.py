from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
import json
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

KAFKA_BROKER = 'localhost:9092'
OUTPUT_TOPIC = 'anomalies'

# Simple connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

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
        print(f"Error connecting to Kafka: {e}")
        return None

async def consume_to_websocket():
    consumer = get_kafka_consumer()
    if not consumer:
        return
    
    # We use await asyncio.sleep(0.01) to yield control back to the event loop
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
        print(f"Kafka consumer error: {e}")
    finally:
        consumer.close()

@app.on_event("startup")
async def startup_event():
    # Start the background task to poll Kafka and push to WebSockets
    asyncio.create_task(consume_to_websocket())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, client might send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
