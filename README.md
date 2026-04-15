# StreamSentinel 🛡️

StreamSentinel is a real-time streaming anomaly detection system. It simulates a stream of financial transactions, processes them in real-time, detects anomalies using a Machine Learning model (Isolation Forest), and visualizes the flow and anomalies on a modern React dashboard.

## Architecture

1. **Kafka / Zookeeper:** Handles real-time messaging of transactions.
2. **Data Generator (`data_generator.py`):** Produces synthetic transaction data (normal and anomalous) and sends them to a Kafka topic (`transactions`).
3. **Anomaly Detector (`anomaly_detector.py`):** Consumes transactions, trains an Isolation Forest model on a sliding window, predicts anomalies, and publishes results to a new Kafka topic (`anomalies`).
4. **Backend (`main.py`):** A FastAPI application that consumes the anomalies and broadcasts them to connected clients via WebSockets.
5. **Frontend (`frontend/`):** A React.js application using Vite and Chart.js to subscribe to the WebSocket and plot the stream in real-time.

## Prerequisites

- Python 3.9+
- Node.js (v18+)
- Docker and Docker Compose

## Quick Start

### 1. Start Infrastructure (Kafka & Zookeeper)

```bash
docker-compose up -d
```

*Note: Ensure Docker Desktop is running before executing this command.*

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Data Pipeline

Open separate terminals for each of the following components:

**Data Generator:**
```bash
python data_generator.py
```

**Anomaly Detector:**
```bash
python anomaly_detector.py
```

**FastAPI Backend:**
```bash
uvicorn main:app --reload --port 8000
```

### 4. Start the Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Navigate to the provided localhost URL (e.g., `http://localhost:5173`) to view the real-time dashboard.
