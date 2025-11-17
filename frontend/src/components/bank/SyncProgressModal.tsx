import { Modal, Progress, Spin, Typography, Result } from 'antd'
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { bankTransactionsApi } from '@/api'

const { Text, Paragraph } = Typography

interface SyncProgressModalProps {
  open: boolean
  taskId: string | null
  onComplete: (success: boolean, result?: any) => void
  onCancel: () => void
}

export const SyncProgressModal = ({ open, taskId, onComplete, onCancel }: SyncProgressModalProps) => {
  const [status, setStatus] = useState<'STARTED' | 'COMPLETED' | 'FAILED'>('STARTED')
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('Запуск синхронизации...')
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!taskId || !open) return

    let pollCount = 0
    const maxPolls = 120 // 10 минут (120 * 5 сек)
    let timeoutId: ReturnType<typeof setTimeout>

    const pollStatus = async () => {
      try {
        const statusResponse = await bankTransactionsApi.getSyncStatus(taskId)

        if (statusResponse.status === 'COMPLETED') {
          setStatus('COMPLETED')
          setProgress(100)
          setMessage('Синхронизация завершена успешно!')
          setResult(statusResponse.result)

          setTimeout(() => {
            onComplete(true, statusResponse.result)
          }, 2000)
        } else if (statusResponse.status === 'FAILED') {
          setStatus('FAILED')
          setMessage('Синхронизация не удалась')
          setError(statusResponse.error || 'Неизвестная ошибка')

          setTimeout(() => {
            onComplete(false)
          }, 3000)
        } else if (statusResponse.status === 'STARTED') {
          // Обновляем прогресс (симуляция)
          pollCount++
          const estimatedProgress = Math.min((pollCount / maxPolls) * 100, 95)
          setProgress(estimatedProgress)
          setMessage(`Синхронизация в процессе... (проверка ${pollCount}/${maxPolls})`)

          if (pollCount < maxPolls) {
            timeoutId = setTimeout(pollStatus, 5000)
          } else {
            setStatus('FAILED')
            setMessage('Превышено время ожидания')
            setError('Синхронизация не завершилась за отведенное время')
          }
        }
      } catch (error: any) {
        console.error('Failed to poll sync status:', error)
        // Продолжаем polling даже при ошибках
        pollCount++
        if (pollCount < maxPolls) {
          timeoutId = setTimeout(pollStatus, 5000)
        }
      }
    }

    // Начать polling через 2 секунды
    timeoutId = setTimeout(pollStatus, 2000)

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [taskId, open])

  const renderContent = () => {
    if (status === 'COMPLETED' && result) {
      return (
        <Result
          status="success"
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          title="Синхронизация завершена!"
          subTitle={
            <div style={{ textAlign: 'left' }}>
              <Paragraph>
                <Text strong>Обработано:</Text> {result.total_fetched || 0} документов
              </Paragraph>
              <Paragraph>
                <Text strong>Создано:</Text> <Text type="success">{result.created || 0}</Text>
                {' | '}
                <Text strong>Обновлено:</Text> <Text type="warning">{result.updated || 0}</Text>
                {' | '}
                <Text strong>Пропущено:</Text> <Text type="secondary">{result.skipped || 0}</Text>
              </Paragraph>
              {result.auto_categorized > 0 && (
                <Paragraph>
                  <Text strong>Автоматически категоризировано:</Text>{' '}
                  <Text type="success">{result.auto_categorized}</Text>
                </Paragraph>
              )}
            </div>
          }
        />
      )
    }

    if (status === 'FAILED') {
      return (
        <Result
          status="error"
          icon={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
          title="Ошибка синхронизации"
          subTitle={error || 'Произошла неизвестная ошибка'}
        />
      )
    }

    return (
      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
        <Spin
          indicator={<LoadingOutlined style={{ fontSize: 48, color: '#1890ff' }} spin />}
          size="large"
        />
        <div style={{ marginTop: 24 }}>
          <Progress
            percent={Math.round(progress)}
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <Paragraph style={{ marginTop: 16, fontSize: 16 }}>
            <Text>{message}</Text>
          </Paragraph>
          <Paragraph type="secondary" style={{ fontSize: 14 }}>
            Пожалуйста, подождите. Не закрывайте окно.
          </Paragraph>
        </div>
      </div>
    )
  }

  return (
    <Modal
      title={<span style={{ fontSize: 18, fontWeight: 600 }}>Синхронизация с 1С</span>}
      open={open}
      onCancel={status !== 'STARTED' ? onCancel : undefined}
      footer={null}
      closable={status !== 'STARTED'}
      maskClosable={false}
      width={600}
      centered
    >
      {renderContent()}
    </Modal>
  )
}

export default SyncProgressModal
