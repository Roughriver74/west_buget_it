import { Modal, Table, Select, Alert, Space, Tag, Typography } from 'antd'
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'

const { Text } = Typography

interface ColumnMappingModalProps {
  open: boolean
  onCancel: () => void
  onConfirm: (mapping: Record<string, string>) => void
  previewData: {
    columns: string[]
    detected_mapping: Record<string, string>
    sample_data: Record<string, any>[]
    total_rows: number
    required_fields: Record<string, string>
  } | null
  loading?: boolean
}

const ColumnMappingModal: React.FC<ColumnMappingModalProps> = ({
  open,
  onCancel,
  onConfirm,
  previewData,
  loading = false,
}) => {
  const [mapping, setMapping] = useState<Record<string, string>>({})

  // Initialize mapping with detected values
  useEffect(() => {
    if (previewData?.detected_mapping) {
      setMapping(previewData.detected_mapping)
    }
  }, [previewData])

  if (!previewData) return null

  const { columns, sample_data, total_rows, required_fields } = previewData

  // Check if required fields are mapped
  const hasDate = !!mapping.date
  // Amount can be either a single 'amount' field or any of the extended fields
  const hasAmount = !!(
    mapping.amount ||
    mapping.amount_rub_credit ||
    mapping.amount_rub_debit ||
    mapping.amount_eur_credit ||
    mapping.amount_eur_debit
  )
  const canProceed = hasDate && hasAmount

  const handleFieldChange = (field: string, column: string | null) => {
    setMapping(prev => {
      const newMapping = { ...prev }
      if (column === null) {
        delete newMapping[field]
      } else {
        newMapping[field] = column
      }
      return newMapping
    })
  }

  const fieldOptions = Object.entries(required_fields).map(([field, label]) => ({
    field,
    label,
    // Only 'date' is strictly required; for amounts we need at least one of the amount fields
    required: field === 'date',
  }))

  const tableColumns = [
    {
      title: 'Поле в системе',
      dataIndex: 'label',
      key: 'label',
      width: 250,
      render: (text: string, record: any) => (
        <Space>
          <Text strong>{text}</Text>
          {record.required && <Tag color="red">обязательно</Tag>}
        </Space>
      ),
    },
    {
      title: 'Колонка в файле',
      dataIndex: 'field',
      key: 'column',
      render: (field: string) => (
        <Select
          style={{ width: '100%' }}
          placeholder="Не использовать"
          allowClear
          value={mapping[field] || undefined}
          onChange={(value) => handleFieldChange(field, value)}
          options={columns.map(col => ({ value: col, label: col }))}
        />
      ),
    },
    {
      title: 'Пример данных',
      key: 'sample',
      render: (_: any, record: any) => {
        const column = mapping[record.field]
        if (!column) return <Text type="secondary">—</Text>

        const samples = sample_data
          .slice(0, 3)
          .map(row => row[column])
          .filter(val => val != null)

        return (
          <div>
            {samples.map((val, idx) => (
              <div key={idx} style={{ fontSize: 12, color: '#666' }}>
                {String(val).substring(0, 50)}
              </div>
            ))}
          </div>
        )
      },
    },
  ]

  return (
    <Modal
      title="Сопоставление колонок"
      open={open}
      onCancel={onCancel}
      onOk={() => onConfirm(mapping)}
      okText="Импортировать"
      cancelText="Отмена"
      width={900}
      okButtonProps={{ disabled: !canProceed, loading }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Info */}
        <Alert
          message={`Обнаружено ${total_rows} строк в файле`}
          description="Укажите, какие колонки из вашего файла соответствуют полям системы. Поле 'Дата' обязательно. Для сумм укажите либо колонку 'Сумма', либо колонки 'Приход руб/Расход руб'."
          type="info"
          showIcon
        />

        {/* Warning if required fields missing */}
        {!canProceed && (
          <Alert
            message="Не хватает обязательных полей"
            description={
              <Space direction="vertical">
                {!hasDate && <div>• Укажите колонку с датой операции</div>}
                {!hasAmount && (
                  <div>• Укажите колонки с суммами (Приход руб/Расход руб или единую колонку Сумма)</div>
                )}
              </Space>
            }
            type="warning"
            showIcon
            icon={<WarningOutlined />}
          />
        )}

        {/* Success if all required fields present */}
        {canProceed && (
          <Alert
            message="Готово к импорту"
            description="Все обязательные поля сопоставлены"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
          />
        )}

        {/* Mapping table */}
        <Table
          columns={tableColumns}
          dataSource={fieldOptions}
          rowKey="field"
          pagination={false}
          size="small"
        />

        {/* Preview data */}
        <div>
          <Text strong>Предпросмотр данных (первые 3 строки):</Text>
          <Table
            dataSource={sample_data.slice(0, 3)}
            columns={columns.map(col => ({
              title: col,
              dataIndex: col,
              key: col,
              ellipsis: true,
              width: 150,
              render: (value: any) => {
                if (value == null) return <Text type="secondary">—</Text>
                return <div style={{ fontSize: 12 }}>{String(value)}</div>
              },
            }))}
            rowKey={(record, idx) => `preview-row-${idx}`}
            pagination={false}
            size="small"
            scroll={{ x: columns.length * 150 }}
          />
        </div>
      </Space>
    </Modal>
  )
}

export default ColumnMappingModal
