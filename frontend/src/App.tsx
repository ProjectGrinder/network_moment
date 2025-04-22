import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Register from './pages/Register'
import Chat from './pages/Chat'
import { WebSocketProvider } from './components/WebSocketProvider'

function App() {
  return (
    <WebSocketProvider location={import.meta.env.VITE_API_URL}>
      <Router>
        <Routes>
          <Route path="/" element={<Register />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Router>
    </WebSocketProvider>
  )
}

export default App
