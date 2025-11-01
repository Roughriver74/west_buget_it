import { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, DatePicker, InputNumber, message, Tabs } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { expensesApi, categoriesApi, contractorsApi, organizationsApi } from '@/api'
import type { Expense, Attachment } from '@/types'
import { ExpenseStatus } from '@/types'
import AttachmentManager from './AttachmentManager'

const { TextArea } = Input
const { Option } = Select

interface ExpenseFormModalProps {
  visible: boolean
  onCancel: () => void
  expense?: Expense | null
  mode: 'create' | 'edit'
}

const ExpenseFormModal: React.FC<ExpenseFormModalProps> = ({
  visible,
  onCancel,
  expense,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [attachments, setAttachments] = useState<Attachment[]>(expense?.attachments || [])

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  // Fetch contractors
  const { data: contractors } = useQuery({
    queryKey: ['contractors'],
    queryFn: () => contractorsApi.getAll({ is_active: true }),
  })

  // Fetch organizations
  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.getAll({ is_active: true }),
  })

  // Status options
  const statusOptions: { value: ExpenseStatus; label: string }[] = [
    { value: ExpenseStatus.DRAFT, label: 'Черновик' },
    { value: ExpenseStatus.PENDING, label: 'К оплате' },
    { value: ExpenseStatus.PAID, label: 'Оплачена' },
    { value: ExpenseStatus.REJECTED, label: 'Отклонена' },
    { value: ExpenseStatus.CLOSED, label: 'Закрыта' },
  ]

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: any) => expensesApi.create(values),
    onSuccess: () => {
      message.success('Заявка успешно создана')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при создании заявки: ${error.message}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      expensesApi.update(id, values),
    onSuccess: (data) => {
      console.log('✅ Заявка успешно обновлена:', data)
      message.success('Заявка успешно обновлена')
      // Invalidate all expenses queries to ensure fresh data
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      // Also refetch to ensure immediate update
      queryClient.refetchQueries({ queryKey: ['expenses'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      console.error('❌ Ошибка при обновлении заявки:', error)
      console.error('Детали ошибки:', error.response?.data)
      message.error(`Ошибка при обновлении заявки: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Initialize form with expense data when editing
  useEffect(() => {
    if (visible && mode === 'edit' && expense) {
      form.setFieldsValue({
        number: expense.number,
        category_id: expense.category_id,
        contractor_id: expense.contractor_id,
        organization_id: expense.organization_id,
        amount: expense.amount,
        request_date: expense.request_date ? dayjs(expense.request_date) : null,
        payment_date: expense.payment_date ? dayjs(expense.payment_date) : null,
        status: expense.status,
        requester: expense.requester,
        comment: expense.comment,
      })
      setAttachments(expense.attachments || [])
    } else if (visible && mode === 'create') {
      form.setFieldsValue({
        status: 'DRAFT',
        request_date: dayjs(),
      })
      setAttachments([])
    }
  }, [visible, mode, expense, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // Format dates to ISO string with time set to noon to avoid timezone issues
      const formattedValues = {
        ...values,
        request_date: values.request_date
          ? dayjs(values.request_date).hour(12).minute(0).second(0).millisecond(0).toISOString()
          : undefined,
        payment_date: values.payment_date
          ? dayjs(values.payment_date).hour(12).minute(0).second(0).millisecond(0).toISOString()
          : undefined,
        is_paid: values.status === 'PAID',
        is_closed: values.status === 'CLOSED',
      }

      console.log('📤 Отправка данных на сервер:', {
        mode,
        expenseId: expense?.id,
        formattedValues,
        originalRequestDate: expense?.request_date,
        newRequestDate: formattedValues.request_date,
      })

      if (mode === 'create') {
        createMutation.mutate(formattedValues)
      } else if (mode === 'edit' && expense) {
        updateMutation.mutate({ id: expense.id, values: formattedValues })
      }
    } catch (error) {
      console.error('Form validation failed:', error)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title={mode === 'create' ? 'Создание заявки' : 'Редактирование заявки'}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText={mode === 'create' ? 'Создать' : 'Сохранить'}
      cancelText="Отмена"
      width={800}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Tabs
        defaultActiveKey="1"
        items={[
          {
            key: '1',
            label: 'Основная информация',
            children: (
              <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
                <Form.Item
                  name="number"
                  label="Номер заявки"
                  rules={[{ required: true, message: 'Введите номер заявки' }]}
                >
                  <Input placeholder="Например: 0В0В-001627" />
                </Form.Item>

        <Form.Item
          name="organization_id"
          label="Организация"
          rules={[{ required: true, message: 'Выберите организацию' }]}
        >
          <Select placeholder="Выберите организацию">
            {organizations?.map((org) => (
              <Option key={org.id} value={org.id}>
                {org.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="category_id"
          label="Категория расходов"
          rules={[{ required: true, message: 'Выберите категорию' }]}
        >
          <Select
            placeholder="Выберите категорию"
            showSearch
            optionFilterProp="children"
          >
            {categories?.map((cat) => (
              <Option key={cat.id} value={cat.id}>
                {cat.name} ({cat.type})
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="contractor_id" label="Контрагент">
          <Select
            placeholder="Выберите контрагента (опционально)"
            showSearch
            optionFilterProp="children"
            allowClear
          >
            {contractors?.map((contractor) => (
              <Option key={contractor.id} value={contractor.id}>
                {contractor.name}
                {contractor.inn && ` (ИНН: ${contractor.inn})`}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="amount"
          label="Сумма"
          rules={[{ required: true, message: 'Введите сумму' }]}
        >
          <InputNumber<number>
            style={{ width: '100%' }}
            min={0}
            placeholder="Введите сумму"
            formatter={(value) =>
              `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
            }
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
          />
        </Form.Item>

        <Form.Item
          name="request_date"
          label="Дата заявки"
          rules={[{ required: true, message: 'Выберите дату заявки' }]}
        >
          <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
        </Form.Item>

        <Form.Item name="payment_date" label="Дата оплаты">
          <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
        </Form.Item>

        <Form.Item
          name="status"
          label="Статус"
          rules={[{ required: true, message: 'Выберите статус' }]}
        >
          <Select placeholder="Выберите статус">
            {statusOptions.map((option) => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="requester" label="Заявитель">
          <Input placeholder="ФИО заявителя" />
        </Form.Item>

                <Form.Item name="comment" label="Комментарий">
                  <TextArea rows={4} placeholder="Дополнительная информация" />
                </Form.Item>
              </Form>
            ),
          },
          {
            key: '2',
            label: `Файлы ${attachments.length > 0 ? `(${attachments.length})` : ''}`,
            children: (
              <div style={{ marginTop: 20 }}>
                <AttachmentManager
                  expenseId={mode === 'edit' && expense ? expense.id : undefined}
                  attachments={attachments}
                  onAttachmentsChange={setAttachments}
                />
              </div>
            ),
          },
        ]}
      />
    </Modal>
  )
}

export default ExpenseFormModal
