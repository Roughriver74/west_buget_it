import { Spin } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'

interface Props {
  loading: boolean
  tip?: string
  fullscreen?: boolean
  size?: 'small' | 'default' | 'large'
}

/**
 * Global loader component with customizable appearance
 *
 * Usage:
 * <GlobalLoader loading={isLoading} tip="Loading data..." />
 * <GlobalLoader loading={isLoading} fullscreen />
 */
export default function GlobalLoader({
  loading,
  tip = 'Загрузка...',
  fullscreen = false,
  size = 'large'
}: Props) {
  if (!loading) return null

  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 48 : 24 }} spin />

  if (fullscreen) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(4px)'
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <Spin indicator={antIcon} size={size} />
          {tip && (
            <div style={{ marginTop: 16, fontSize: 16, color: '#666' }}>{tip}</div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 200,
        padding: '40px 0'
      }}
    >
      <Spin indicator={antIcon} size={size} tip={tip} />
    </div>
  )
}

/**
 * Inline loader for use within components
 */
export function InlineLoader({ tip = 'Загрузка...', size = 'default' }: Omit<Props, 'loading' | 'fullscreen'>) {
  return (
    <div style={{ textAlign: 'center', padding: '20px 0' }}>
      <Spin size={size} tip={tip} />
    </div>
  )
}

/**
 * Page loader - takes full page height
 */
export function PageLoader({ tip = 'Загрузка страницы...', loading = true }: Omit<Props, 'fullscreen' | 'size'>) {
  if (!loading) return null

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 200px)',
        flexDirection: 'column'
      }}
    >
      <Spin size="large" />
      <div style={{ marginTop: 16, fontSize: 16, color: '#666' }}>{tip}</div>
    </div>
  )
}
