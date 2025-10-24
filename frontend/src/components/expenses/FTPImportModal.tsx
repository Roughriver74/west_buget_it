import { useState } from 'react'
import { Modal, Form, Input, InputNumber, message, Alert, Statistic, Row, Col, Switch } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi } from '@/api'

interface FTPImportModalProps {
  visible: boolean
  onCancel: () => void
}

interface ImportResult {
  success: boolean
  message: string
  statistics: {
    deleted: number
    created: number
    updated: number
    skipped: number
    total_in_file: number
  }
}

const FTPImportModal: React.FC<FTPImportModalProps> = ({ visible, onCancel }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [importResult, setImportResult] = useState<ImportResult | null>(null)

  const importMutation = useMutation({
    mutationFn: async (values: any) => {
      const response = await expensesApi.importFromFTP(values)
      return response
    },
    onSuccess: (data) => {
      setImportResult(data)
      message.success('Импорт завершён успешно!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка импорта: ${error.message || 'Неизвестная ошибка'}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await importMutation.mutateAsync(values)
    } catch (error) {
      console.error('Form validation failed:', error)
    }
  }

  const handleCancel = () => {
    if (!importMutation.isPending) {
      form.resetFields()
      setImportResult(null)
      onCancel()
    }
  }

  const handleClose = () => {
    form.resetFields()
    setImportResult(null)
    onCancel()
  }

  return (
    <Modal
      title="Импорт заявок из FTP"
      open={visible}
      onOk={importResult ? handleClose : handleSubmit}
      onCancel={handleCancel}
      okText={importResult ? 'Закрыть' : 'Начать импорт'}
      cancelText="Отмена"
      width={700}
      confirmLoading={importMutation.isPending}
      cancelButtonProps={{ disabled: importMutation.isPending }}
    >
      {!importResult ? (
        <>
          <Alert
            message="Информация"
            description="Импорт загрузит данные из файла на FTP сервере. Дубликаты будут автоматически пропущены."
            type="info"
            showIcon
            style={{ marginBottom: 20 }}
          />

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              remote_path: '/Zayavki na raszkhod(spisok) XLSX.xlsx',
              skip_duplicates: true,
            }}
          >
            <Form.Item
              name="remote_path"
              label="Путь к файлу на FTP"
              rules={[{ required: true, message: 'Укажите путь к файлу' }]}
              extra="Файл на сервере: Zayavki na raszkhod(spisok) XLSX.xlsx"
            >
              <Input placeholder="/Zayavki na raszkhod(spisok) XLSX.xlsx" />
            </Form.Item>

            <Form.Item
              name="skip_duplicates"
              label="Пропускать дубликаты"
              valuePropName="checked"
              extra="При включении, заявки с существующими номерами будут пропущены"
            >
              <Switch />
            </Form.Item>

            <Alert
              message="Информация о сервере"
              description={
                <div>
                  <p><strong>Сервер:</strong> floppisw.beget.tech</p>
                  <p><strong>Логин:</strong> floppisw_zrds</p>
                  <p style={{ marginBottom: 0 }}><strong>Статус:</strong> Подключение автоматическое</p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Form>
        </>
      ) : (
        <>
          <Alert
            message="Импорт завершён успешно!"
            description={importResult.message}
            type="success"
            showIcon
            style={{ marginBottom: 20 }}
          />

          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Statistic
                title="Удалено старых записей"
                value={importResult.statistics.deleted}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Всего в файле"
                value={importResult.statistics.total_in_file}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Создано новых"
                value={importResult.statistics.created}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Обновлено"
                value={importResult.statistics.updated}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Пропущено"
                value={importResult.statistics.skipped}
                valueStyle={{ color: '#faad14' }}
              />
            </Col>
          </Row>
        </>
      )}
    </Modal>
  )
}

export default FTPImportModal
