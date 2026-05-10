import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TonConnectUIProvider } from '@tonconnect/ui-react'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const MANIFEST_URL =
  import.meta.env.VITE_MANIFEST_URL ||
<<<<<<< HEAD
  'http://localhost:8080/tonconnect-manifest.json'
=======
  'https://frontend-yegor121.vercel.app/tonconnect-manifest.json'
>>>>>>> dca578408c1ff45c1b18f8b91ce36fccb8b582ec

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TonConnectUIProvider manifestUrl={MANIFEST_URL}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </TonConnectUIProvider>
  </React.StrictMode>,
)
