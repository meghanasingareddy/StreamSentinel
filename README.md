# StreamSentinel 🛡️ [Enterprise Edition]

StreamSentinel is an industry-grade, real-time anomaly detection system. It processes a simulated stream of financial transactions, detects anomalies on-the-fly using an Isolation Forest Machine Learning model, broadcasts alerts via an alerting microservice, and visualizes the flow on a modern React dashboard.

## 📌 Problem Statement
In financial systems, fraudulent transactions happen in milliseconds. Batch processing (e.g., cron jobs analyzing DB records nightly) is too slow to stop fraud. We need a system that ingests streaming data, predicts anomalies in real-time within a sliding window, and instantly triggers alerts and live dashboard updates.

## 🏛️ Architecture

StreamSentinel uses a fully containerized microservice architecture, orchestrated by Docker Compose:

```text
                                  ┌───────────────────────────┐
                                  │   React Dashboard (Vite)  │
                                  └─────────────▲─────────────┘
                                                │ (WebSockets)
 ┌──────────────┐         ┌───────────┐   ┌─────┴───────────┐
 │ Data         │ (JSON)  │ Kafka     │   │ API Gateway     │ (FastAPI)
 │ Generator    ├────────►│ Broker    ├──►│ (Consumer)      │
 │ (Producer)   │         │           │   └─────────────────┘
 └──────────────┘         └─────▲─┬───┘
                                │ │
 ┌──────────────┐   (Consume)   │ │  (Produce)  ┌─────────────────┐
 │ Anomaly      ├───────────────┘ └────────────►│ Alerting        │ (Alert via
 │ Detector     │                               │ Service         │  Slack/Email)
 │ (ML Model)   │                               └─────────────────┘
 └──────────────┘
```

## 🛠️ Tech Stack
- **Message Broker:** Apache Kafka & Zookeeper
- **Backend / Microservices:** Python 3.10, FastAPI, Kafka-Python
- **Machine Learning:** Scikit-Learn (Isolation Forest), Pandas, NumPy
- **Frontend Dashboard:** React.js, Vite, Chart.js, Tailwind/Vanilla CSS
- **Infrastructure:** Docker, Docker Compose

## 🚀 How to Run locally

### 1. Start the Backend Infrastructure
Ensure Docker Desktop is running, then spin up Kafka, Zookeeper, and all 4 Python microservices with a single command:

```bash
docker-compose up --build -d
```
*This will start the data generator, the ML detector, the API gateway (port 8000), and the Alerting Service.*

### 2. Start the Frontend Dashboard
Open a terminal in the `frontend` folder:

```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`. You will see real-time transactions plotting on the chart. Anomalies will spike in red!

## 🧪 Sample Output

**Data Generator Log:**
```text
[INFO] DataGenerator - Produced transaction 8f8d9b-11 (Amount: $15.50)
[INFO] DataGenerator - Produced transaction a12b4c-9f (Amount: $18400.00)  <-- Artificial Anomaly
```

**Alerting Service Log:**
```text
[ERROR] AlertingService - FIRING ALERT -> 🚨 *CRITICAL ALERT: Anomaly Detected!* 🚨
Transaction ID: a12b4c-9f
User ID: user_42
Amount: $18400.00
Action Required: Immediate review of account activity.
```

## 🌍 Suggestion for Cloud Deployment

To take this live, here is the recommended deployment strategy:

1. **Kafka Cluster:** Setup a managed Kafka instance using **Confluent Cloud** or **Upstash**.
2. **Microservices (Python):** Deploy the `Dockerfile` for each microservice using **Render**, **Railway**, or **AWS ECS**. Set the `KAFKA_BROKER` environment variable to your managed Kafka URL.
3. **Frontend:** Deploy the Vite React app to **Vercel** or **Netlify**. Ensure the WebSocket URL points to your Render/Railway API Gateway deployment.

## 📈 Future Improvements for Production

- **Persistent Storage:** Add a database (e.g., PostgreSQL or ClickHouse) to permanently store historical transaction data.
- **Model Registry:** Use MLflow to track, version, and load the Isolation Forest model dynamically from an S3 bucket instead of training from scratch on startup.
- **Observability:** Replace console logging with a proper APM tool like Datadog or Prometheus/Grafana to monitor Kafka consumer lag and model drift.
