import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SecurityDashboard from './SecurityDashboard.jsx'
import Recordings from './Recordings.jsx'

function App() {
  const [page, setPage] = useState('live')
  if (page === 'recordings') return <Recordings onNavigate={setPage} />
  return <SecurityDashboard onNavigate={setPage} />
}

createRoot(document.getElementById('root')).render(<App />)
