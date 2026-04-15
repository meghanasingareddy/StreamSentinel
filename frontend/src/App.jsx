import { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { Activity, ShieldAlert, Zap, RadioTower } from 'lucide-react'
import './index.css'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

function App() {
  const [dataPoints, setDataPoints] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [stats, setStats] = useState({
    totalProcessed: 0,
    anomaliesDetected: 0,
    currentRate: 0
  })

  useEffect(() => {
    // Only keeping last 50 points to maintain performance
    const maxDataPoints = 50
    let lastMessageTime = Date.now()
    let messageCountInWindow = 0
    let intervalId = null;

    const connectWebSocket = () => {
      // Connect to the backend WebSocket
      const ws = new WebSocket('ws://localhost:8000/ws')

      ws.onopen = () => {
        console.log('Connected to StreamSentinel WebSocket')
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        messageCountInWindow++
        const tx = JSON.parse(event.data)
        
        // Ensure values exist
        const amount = Number(tx.amount || 0)
        const isAnomaly = tx.ml_anomaly || tx.is_synthetic_anomaly || false
        
        setDataPoints(current => {
          const newPoints = [...current, {
            time: new Date().toLocaleTimeString(),
            amount: amount,
            anomaly: isAnomaly
          }]
          
          if (newPoints.length > maxDataPoints) {
            newPoints.shift()
          }
          return newPoints
        })

        setStats(prev => ({
          ...prev,
          totalProcessed: prev.totalProcessed + 1,
          anomaliesDetected: prev.anomaliesDetected + (isAnomaly ? 1 : 0)
        }))
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected, attempting reconnect...')
        setTimeout(connectWebSocket, 3000)
      }
      
      return ws;
    }

    const ws = connectWebSocket();

    // Calculate events per second
    intervalId = setInterval(() => {
      const now = Date.now()
      const elapsedSecs = (now - lastMessageTime) / 1000
      if (elapsedSecs > 0) {
          setStats(prev => ({
              ...prev,
              currentRate: Math.round(messageCountInWindow / elapsedSecs)
          }))
      }
      messageCountInWindow = 0
      lastMessageTime = now
    }, 1000)

    return () => {
      ws.close()
      clearInterval(intervalId)
    }
  }, [])

  // Prepare chart data
  const chartData = {
    labels: dataPoints.map(d => d.time),
    datasets: [
      {
        label: 'Transaction Amount',
        data: dataPoints.map(d => d.amount),
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.5)',
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 0
      },
      {
        label: 'Anomalies',
        data: dataPoints.map(d => d.anomaly ? d.amount : null),
        borderColor: '#ef4444',
        backgroundColor: '#ef4444',
        pointBackgroundColor: '#ef4444',
        pointBorderColor: '#fff',
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: false
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 0 // Disable animation for actual realtime feel
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false
        },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: {
          display: false,
          drawBorder: false
        },
        ticks: { 
          color: '#94a3b8',
          maxTicksLimit: 8
        }
      }
    },
    plugins: {
      legend: {
        labels: {
          color: '#f8fafc',
          usePointStyle: true,
          boxWidth: 8
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12
      }
    }
  }

  const hasRecentAnomaly = dataPoints.slice(-5).some(d => d.anomaly)

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <Activity className="logo-icon" size={32} />
          <h1>StreamSentinel</h1>
        </div>
        <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator"></div>
          {isConnected ? 'Live Stream Active' : 'Connecting...'}
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <Zap size={28} />
          </div>
          <div className="stat-info">
            <h3>Events Processed</h3>
            <div className="stat-value">{stats.totalProcessed.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon-wrapper red">
            <ShieldAlert size={28} />
          </div>
          <div className="stat-info">
            <h3>Anomalies Detected</h3>
            <div className="stat-value error">{stats.anomaliesDetected.toLocaleString()}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <RadioTower size={28} />
          </div>
          <div className="stat-info">
            <h3>Processing Rate</h3>
            <div className="stat-value">{stats.currentRate} <span style={{fontSize: '1rem', color: '#94a3b8', fontWeight: 500}}>tx/sec</span></div>
          </div>
        </div>
      </div>

      <div className="chart-section">
        <div className="chart-header">
          <h2>Real-time Transaction Monitor</h2>
          {hasRecentAnomaly && (
            <div className="alert-pulse">Anomaly Detected!</div>
          )}
        </div>
        
        <div className="chart-container">
          {dataPoints.length > 0 ? (
            <Line options={chartOptions} data={chartData} />
          ) : (
            <div className="empty-state">
              <div className="spinner"></div>
              <p>Waiting for transaction data...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
