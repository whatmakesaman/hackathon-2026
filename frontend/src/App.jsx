import { Route, Routes } from 'react-router-dom'
import Simulator from './pages/Simulator'
import Result from './pages/Result'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Simulator />} />
      <Route path="/result/:id" element={<Result />} />
    </Routes>
  )
}
