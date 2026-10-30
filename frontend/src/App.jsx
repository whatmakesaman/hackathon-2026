import { Route, Routes } from 'react-router-dom'
import Simulator from './pages/Simulator'
import Result from './pages/Result'
import useInbox from './useInbox'

export default function App() {
  const { inbox, addMessage } = useInbox()
  return (
    <Routes>
      <Route path="/" element={<Simulator inbox={inbox} addMessage={addMessage} />} />
      <Route path="/result/:id" element={<Result />} />
    </Routes>
  )
}
