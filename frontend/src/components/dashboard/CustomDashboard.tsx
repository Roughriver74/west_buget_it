import React, { useState } from 'react'
import { Button, Space, message, Modal, Form, Input, Select } from 'antd'
import { SaveOutlined, PlusOutlined, SettingOutlined } from '@ant-design/icons'
import type { DashboardConfig, Widget } from '@/types'
import WidgetRenderer from './widgets'
import './CustomDashboard.css'

const { Option } = Select

interface CustomDashboardProps {
  config: DashboardConfig
  onSave?: (config: DashboardConfig) => void
  editable?: boolean
}

const WIDGET_TYPES = [
  { value: 'total_amount', label: 'Общая сумма' },
  { value: 'category_chart', label: 'График по категориям' },
  { value: 'monthly_trend', label: 'Месячный тренд' },
  { value: 'recent_expenses', label: 'Последние расходы' },
]

const CustomDashboard: React.FC<CustomDashboardProps> = ({
  config,
  onSave,
  editable = false,
}) => {
  const [widgets, setWidgets] = useState<Widget[]>(config.config.widgets || [])
  const [addModalVisible, setAddModalVisible] = useState(false)
  const [form] = Form.useForm()

  const handleSave = () => {
    if (onSave) {
      onSave({
        ...config,
        config: {
          widgets,
        },
      })
      message.success('Дашборд сохранен')
    }
  }

  const handleAddWidget = () => {
    form.validateFields().then((values) => {
      const newWidget: Widget = {
        id: `widget-${Date.now()}`,
        type: values.type,
        title: values.title,
        config: {},
        layout: {
          x: 0,
          y: widgets.length,
          w: values.type === 'total_amount' ? 3 : 6,
          h: values.type === 'total_amount' ? 2 : 4,
        },
      }

      setWidgets([...widgets, newWidget])
      setAddModalVisible(false)
      form.resetFields()
      message.success('Виджет добавлен')
    })
  }

  const handleRemoveWidget = (widgetId: string) => {
    setWidgets(widgets.filter((w) => w.id !== widgetId))
    message.success('Виджет удален')
  }

  return (
    <div>
      {editable && (
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddModalVisible(true)}
          >
            Добавить виджет
          </Button>
          <Button icon={<SaveOutlined />} onClick={handleSave}>
            Сохранить
          </Button>
        </Space>
      )}

      <div className="dashboard-grid">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className="dashboard-widget"
            style={{
              gridColumn: `span ${widget.layout.w}`,
              gridRow: `span ${widget.layout.h}`,
            }}
          >
            {editable && (
              <div className="widget-controls">
                <Button
                  size="small"
                  danger
                  onClick={() => handleRemoveWidget(widget.id)}
                >
                  Удалить
                </Button>
              </div>
            )}
            <WidgetRenderer widget={widget} />
          </div>
        ))}
      </div>

      <Modal
        title="Добавить виджет"
        open={addModalVisible}
        onOk={handleAddWidget}
        onCancel={() => {
          setAddModalVisible(false)
          form.resetFields()
        }}
        okText="Добавить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="Название"
            rules={[{ required: true, message: 'Введите название виджета' }]}
          >
            <Input placeholder="Например: Расходы за месяц" />
          </Form.Item>

          <Form.Item
            name="type"
            label="Тип виджета"
            rules={[{ required: true, message: 'Выберите тип виджета' }]}
          >
            <Select placeholder="Выберите тип">
              {WIDGET_TYPES.map((type) => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default CustomDashboard
