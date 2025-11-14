import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, App as AntApp } from 'antd'
import ruRU from 'antd/locale/ru_RU'
import dayjs from 'dayjs'
import 'dayjs/locale/ru'
import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/react'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './config/axiosConfig' // Global axios configuration with auth interceptors
import './index.css'

dayjs.locale('ru')

// Handle chunk load errors (happens after deployments when old chunks are gone)
window.addEventListener('error', (event) => {
  const isChunkLoadError = event.message?.includes('Failed to fetch dynamically imported module') ||
                          event.message?.includes('Importing a module script failed') ||
                          event.message?.includes('error loading dynamically imported module')

  if (isChunkLoadError) {
    // Check if we already tried to reload (avoid infinite loop)
    const hasReloaded = sessionStorage.getItem('chunk-load-error-reloaded')
    if (!hasReloaded) {
      sessionStorage.setItem('chunk-load-error-reloaded', 'true')
      console.log('Chunk load error detected, reloading page...')
      window.location.reload()
    } else {
      console.error('Chunk load error persists after reload')
    }
  }
})

// Clear reload flag on successful load
window.addEventListener('load', () => {
  sessionStorage.removeItem('chunk-load-error-reloaded')
})

const sentryDsn = import.meta.env.VITE_SENTRY_DSN as string | undefined
if (sentryDsn) {
  const tracesSampleRate = Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? '0')
  Sentry.init({
    dsn: sentryDsn,
    integrations: [new BrowserTracing()],
    tracesSampleRate: Number.isFinite(tracesSampleRate) ? tracesSampleRate : 0,
    environment: import.meta.env.MODE,
  })
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={ruRU}>
          <AntApp>
            <App />
          </AntApp>
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
