import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initSession } from './api'

const root = createRoot(document.getElementById('root')!)

async function start() {
  try {
    await initSession()
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch (e) {
    console.error(e)
    root.render(<p>Nie można połączyć się z serwerem.</p>)
  }
}

start()