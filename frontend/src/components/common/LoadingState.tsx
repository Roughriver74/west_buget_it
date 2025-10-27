import type { CSSProperties, ReactNode } from 'react'
import { Spin, Typography } from 'antd'

type LoadingStateProps = {
  message?: ReactNode
  fullHeight?: boolean
  style?: CSSProperties
}

const containerStyle = (fullHeight: boolean, style?: CSSProperties): CSSProperties => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 48,
  minHeight: fullHeight ? '40vh' : undefined,
  ...style,
})

const LoadingState = ({ message = 'Загрузка данных…', fullHeight = true, style }: LoadingStateProps) => (
  <div style={containerStyle(fullHeight, style)}>
    <Spin size="large" />
    {message && (
      <Typography.Text type="secondary" style={{ marginTop: 16, textAlign: 'center' }}>
        {message}
      </Typography.Text>
    )}
  </div>
)

export default LoadingState
