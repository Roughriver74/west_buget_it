import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Select, Button, Space, message, Modal, Form, Input } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import axios from 'axios'
import CustomDashboard from '@/components/dashboard/CustomDashboard'
import type { DashboardConfig } from '@/types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const { Option } = Select

const CustomDashboardPage = () => {
  const [selectedDashboardId, setSelectedDashboardId] = useState<number | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // Fetch dashboards
  const { data: dashboards } = useQuery({
    queryKey: ['dashboards'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/dashboards`)
      return response.data.items
    },
  })

  // Fetch selected dashboard
  const { data: selectedDashboard, isLoading } = useQuery({
    queryKey: ['dashboard', selectedDashboardId],
    queryFn: async () => {
      if (!selectedDashboardId) return null
      const response = await axios.get(`${API_BASE}/dashboards/${selectedDashboardId}`)
      return response.data
    },
    enabled: !!selectedDashboardId,
  })

  // Update dashboard mutation
  const updateMutation = useMutation({
    mutationFn: async (config: DashboardConfig) => {
      await axios.patch(`${API_BASE}/dashboards/${config.id}`, {
        config: config.config,
      })
    },
    onSuccess: () => {
      message.success('Дашборд обновлен')
      queryClient.invalidateQueries({ queryKey: ['dashboard', selectedDashboardId] })
      setEditMode(false)
    },
    onError: () => {
      message.error('Ошибка при обновлении дашборда')
    },
  })

  // Create dashboard mutation
  const createMutation = useMutation({
    mutationFn: async (values: any) => {
      const response = await axios.post(`${API_BASE}/dashboards`, {
        name: values.name,
        description: values.description,
        is_default: false,
        is_public: true,
        config: {
          widgets: [],
        },
      })
      return response.data
    },
    onSuccess: (data) => {
      message.success('Дашборд создан')
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
      setSelectedDashboardId(data.id)
      setCreateModalVisible(false)
      setEditMode(true)
      form.resetFields()
    },
    onError: () => {
      message.error('Ошибка при создании дашборда')
    },
  })

  const handleSave = (config: DashboardConfig) => {
    updateMutation.mutate(config)
  }

  const handleCreate = () => {
    form.validateFields().then((values) => {
      createMutation.mutate(values)
    })
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Select
            style={{ width: 300 }}
            placeholder="Выберите дашборд"
            value={selectedDashboardId}
            onChange={setSelectedDashboardId}
          >
            {dashboards?.map((dashboard: DashboardConfig) => (
              <Option key={dashboard.id} value={dashboard.id}>
                {dashboard.name}
                {dashboard.is_default && ' (по умолчанию)'}
              </Option>
            ))}
          </Select>

          <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            Создать дашборд
          </Button>

          {selectedDashboardId && !editMode && (
            <Button icon={<EditOutlined />} onClick={() => setEditMode(true)}>
              Редактировать
            </Button>
          )}

          {editMode && (
            <Button onClick={() => setEditMode(false)}>Отменить редактирование</Button>
          )}
        </Space>
      </div>

      {selectedDashboard && (
        <CustomDashboard
          config={selectedDashboard}
          onSave={handleSave}
          editable={editMode}
        />
      )}

      {!selectedDashboard && !isLoading && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          Выберите дашборд или создайте новый
        </div>
      )}

      <Modal
        title="Создать дашборд"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название дашборда' }]}
          >
            <Input placeholder="Например: Мой дашборд" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} placeholder="Описание дашборда (опционально)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default CustomDashboardPage
