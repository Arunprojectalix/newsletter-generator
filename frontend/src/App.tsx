import { Routes, Route, Navigate } from 'react-router-dom'
import NeighborhoodForm from './pages/NeighborhoodForm'
import ChatInterface from './pages/ChatInterface'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Navigate to="/new" replace />} />
        <Route path="/new" element={<NeighborhoodForm />} />
        <Route path="/chat/:neighborhoodId" element={<ChatInterface />} />
      </Routes>
    </div>
  )
}

export default App
