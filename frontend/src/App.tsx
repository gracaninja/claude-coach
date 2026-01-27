import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Sessions from './pages/Sessions'
import SessionDetail from './pages/SessionDetail'
import Analytics from './pages/Analytics'
import Insights from './pages/Insights'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sessions" element={<Sessions />} />
        <Route path="sessions/:sessionId" element={<SessionDetail />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="insights" element={<Insights />} />
      </Route>
    </Routes>
  )
}

export default App
