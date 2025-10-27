import type { ReactNode } from 'react'
import { Result, Button } from 'antd'

type ErrorStatus = 'error' | 'warning' | 'info' | '500' | '404'

type ErrorStateProps = {
  status?: ErrorStatus
  title?: ReactNode
  description?: ReactNode
  onRetry?: () => void
  retryLabel?: string
  extra?: ReactNode
  fullHeight?: boolean
}

const ErrorState = ({
  status = 'error',
  title = 'Не удалось загрузить данные',
  description,
  onRetry,
  retryLabel = 'Повторить попытку',
  extra,
  fullHeight = true,
}: ErrorStateProps) => {
  const actions = [
    onRetry && (
      <Button key="retry" type="primary" onClick={onRetry}>
        {retryLabel}
      </Button>
    ),
    extra,
  ].filter(Boolean) as ReactNode[]

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 32,
        minHeight: fullHeight ? '40vh' : undefined,
      }}
    >
      <Result status={status} title={title} subTitle={description} extra={actions.length ? actions : undefined} />
    </div>
  )
}

export default ErrorState
