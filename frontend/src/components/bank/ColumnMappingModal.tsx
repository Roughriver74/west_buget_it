import { Modal, Table, Select, Alert } from 'antd'
import { useState, useEffect } from 'react'

interface ColumnMappingModalProps {
  open: boolean
  onCancel: () => void
  onConfirm: (mapping: Record<string, string>) => void
  previewData: {
    columns: string[]
    detected_mapping: Record<string, string>
    sample_data: Record<string, any>[]
  } | null
  loading?: boolean
}

const ColumnMappingModal = ({
  open,
  onCancel,
  onConfirm,
  previewData,
  loading = false,
}: ColumnMappingModalProps) => {
  const [mapping, setMapping] = useState<Record<string, string>>({})

  useEffect(() => {
    if (previewData?.detected_mapping) {
      setMapping(previewData.detected_mapping)
    }
  }, [previewData])

  if (!previewData) return null

  const handleConfirm = () => {
    onConfirm(mapping)
  }

  const columns = [
    {
      title: 'Колонка в файле',
      dataIndex: 'fileColumn',
      key: 'fileColumn',
    },
    {
      title: 'Пример данных',
      dataIndex: 'sample',
      key: 'sample',
    },
  ]

  const data = previewData.columns.map((col) => ({
    key: col,
    fileColumn: col,
    sample: previewData.sample_data[0]?.[col] || '',
  }))

  return (
    <Modal
      title="Предпросмотр файла"
      open={open}
      onCancel={onCancel}
      onOk={handleConfirm}
      confirmLoading={loading}
      width={800}
      okText="Импортировать"
      cancelText="Отмена"
    >
      <Alert
        message="Файл успешно прочитан"
        description="Нажмите 'Импортировать' для начала импорта данных"
        type="success"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Table
        columns={columns}
        dataSource={data}
        pagination={false}
        size="small"
        scroll={{ y: 400 }}
      />
    </Modal>
  )
}

export default ColumnMappingModal
