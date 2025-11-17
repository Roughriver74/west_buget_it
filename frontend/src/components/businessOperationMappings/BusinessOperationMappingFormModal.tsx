import { useEffect } from 'react'
import { Modal, Form, Input, InputNumber, message, Switch, Select, Slider } from 'antd'
import { useMutation, useQuery } from '@tanstack/react-query'
import * as businessOperationMappingsApi from '@/api/businessOperationMappings'
import { categoriesApi } from '@/api'
import type { BusinessOperationMapping } from '@/types/businessOperationMapping'
import { useDepartment } from '@/contexts/DepartmentContext'

const { TextArea } = Input
const { Option } = Select

interface BusinessOperationMappingFormModalProps {
  visible: boolean
  onClose: () => void
  onSuccess: () => void
  mapping?: BusinessOperationMapping | null
  mode: 'create' | 'edit'
}

const BusinessOperationMappingFormModal: React.FC<BusinessOperationMappingFormModalProps> = ({
  visible,
  onClose,
  onSuccess,
  mapping,
  mode,
}) => {
  const [form] = Form.useForm()
  const { selectedDepartment } = useDepartment()

  // Fetch categories for the dropdown
  const { data: categories } = useQuery({
    queryKey: ['categories', selectedDepartment?.id],
    queryFn: () =>
      categoriesApi.getAll({
        is_active: true,
        department_id: selectedDepartment?.id,
        limit: 1000, // Get all active categories
      }),
    enabled: visible,
  })

  useEffect(() => {
    if (visible && mapping && mode === 'edit') {
      form.setFieldsValue({
        business_operation: mapping.business_operation,
        category_id: mapping.category_id,
        priority: mapping.priority,
        confidence: Math.round(mapping.confidence * 100), // Convert to percentage for slider
        notes: mapping.notes || '',
        is_active: mapping.is_active ?? true,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
      form.setFieldsValue({
        priority: 10,
        confidence: 98,
        is_active: true,
      })
    }
  }, [visible, mapping, mode, form])

  const createMutation = useMutation({
    mutationFn: (values: any) => {
      // Convert confidence back to decimal
      const data = {
        ...values,
        confidence: values.confidence / 100,
        department_id: selectedDepartment?.id,
      }
      return businessOperationMappingsApi.createMapping(data)
    },
    onSuccess: () => {
      message.success('Маппинг успешно создан')
      form.resetFields()
      onSuccess()
    },
    onError: (error: any) => {
      message.error(`Ошибка при создании: ${error.response?.data?.detail || error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) => {
      // Convert confidence back to decimal
      const data = {
        ...values,
        confidence: values.confidence / 100,
      }
      return businessOperationMappingsApi.updateMapping(id, data)
    },
    onSuccess: () => {
      message.success('Маппинг успешно обновлен')
      form.resetFields()
      onSuccess()
    },
    onError: (error: any) => {
      message.error(`Ошибка при обновлении: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (mode === 'create') {
        createMutation.mutate(values)
      } else if (mode === 'edit' && mapping) {
        updateMutation.mutate({ id: mapping.id, values })
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      title={mode === 'create' ? 'Создать маппинг' : 'Редактировать маппинг'}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText={mode === 'create' ? 'Создать' : 'Сохранить'}
      cancelText="Отмена"
      width={700}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          priority: 10,
          confidence: 98,
          is_active: true,
        }}
      >
        <Form.Item
          name="business_operation"
          label="Хозяйственная операция"
          tooltip="Название операции из 1С (например: ОплатаПоставщику, ВыплатаЗарплаты)"
          rules={[
            { required: true, message: 'Введите название операции' },
            { max: 100, message: 'Максимум 100 символов' },
          ]}
        >
          <Input
            placeholder="ОплатаПоставщику"
            disabled={mode === 'edit'} // Cannot change operation name in edit mode
          />
        </Form.Item>

        <Form.Item
          name="category_id"
          label="Категория бюджета"
          tooltip="Категория, к которой будет относиться эта операция"
          rules={[{ required: true, message: 'Выберите категорию' }]}
        >
          <Select
            placeholder="Выберите категорию"
            showSearch
            optionFilterProp="children"
            filterOption={(input, option) =>
              String(option?.children || '').toLowerCase().includes(input.toLowerCase())
            }
          >
            {categories?.map((category) => (
              <Option key={category.id} value={category.id}>
                {category.name} ({category.type})
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="priority"
          label="Приоритет"
          tooltip="Чем выше приоритет, тем раньше применяется маппинг. Диапазон: 1-100"
          rules={[
            { required: true, message: 'Введите приоритет' },
            { type: 'number', min: 1, max: 100, message: 'Приоритет должен быть от 1 до 100' },
          ]}
        >
          <InputNumber
            min={1}
            max={100}
            style={{ width: '100%' }}
            placeholder="10"
          />
        </Form.Item>

        <Form.Item
          name="confidence"
          label="Уверенность (%)"
          tooltip="Уровень уверенности для AI-классификатора. Чем выше, тем надежнее маппинг"
          rules={[
            { required: true, message: 'Укажите уверенность' },
          ]}
        >
          <Slider
            min={0}
            max={100}
            marks={{
              0: '0%',
              50: '50%',
              70: '70%',
              90: '90%',
              100: '100%',
            }}
            tooltip={{ formatter: (value) => `${value}%` }}
          />
        </Form.Item>

        <Form.Item
          name="notes"
          label="Примечания"
          tooltip="Дополнительная информация о маппинге"
        >
          <TextArea
            rows={3}
            placeholder="Например: Используется для оплаты товаров и услуг"
            maxLength={500}
          />
        </Form.Item>

        <Form.Item
          name="is_active"
          label="Активный"
          valuePropName="checked"
          tooltip="Только активные маппинги используются в классификации"
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default BusinessOperationMappingFormModal
