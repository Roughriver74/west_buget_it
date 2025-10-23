import React from 'react'
import { Modal, Form, DatePicker, Select, InputNumber, Input, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { expensesApi, categoriesApi } from '@/api'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

interface QuickExpenseModalProps {
  open: boolean
  onClose: () => void
  defaultMonth?: number
  defaultYear?: number
}

const QuickExpenseModal: React.FC<QuickExpenseModalProps> = ({
  open,
  onClose,
  defaultMonth,
  defaultYear,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // Загрузка списка категорий
  const { data: categories } = useQuery({
    queryKey: ['categories', { is_active: true }],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  const createMutation = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget-overview'] })
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      message.success('Расход успешно добавлен!')
      onClose()
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (values: any) => {
    // Формируем минимальный объект expense
    const expenseData = {
      number: `EXP-${Date.now()}`, // Автогенерация номера
      category_id: values.category_id,
      amount: values.amount,
      request_date: values.request_date.toISOString(),
      status: 'Оплачена', // Сразу помечаем как оплаченную
      is_paid: true,
      is_closed: false,
      organization_id: 1, // Заглушка, потом можно убрать
      comment: values.comment || '',
      // Контрагент как текст в комментарии
      ...(values.contractor_name && {
        comment: `Контрагент: ${values.contractor_name}${values.comment ? '\n' + values.comment : ''}`,
      }),
    }

    createMutation.mutate(expenseData)
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      title="Добавить расход"
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={createMutation.isPending}
      width={500}
      okText="Добавить"
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          request_date: defaultMonth && defaultYear
            ? dayjs().year(defaultYear).month(defaultMonth - 1)
            : dayjs(),
        }}
      >
        <Form.Item
          name="request_date"
          label="Дата расхода"
          rules={[{ required: true, message: 'Выберите дату' }]}
        >
          <DatePicker
            format="DD.MM.YYYY"
            style={{ width: '100%' }}
            placeholder="Выберите дату"
          />
        </Form.Item>

        <Form.Item
          name="category_id"
          label="Статья расходов"
          rules={[{ required: true, message: 'Выберите статью' }]}
        >
          <Select
            placeholder="Выберите статью"
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

        <Form.Item
          name="amount"
          label="Сумма"
          rules={[
            { required: true, message: 'Введите сумму' },
            { type: 'number', min: 0.01, message: 'Сумма должна быть больше 0' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            step={1000}
            placeholder="Введите сумму"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number(value!.replace(/\s?/g, '')) as any}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="contractor_name"
          label="Контрагент (опционально)"
        >
          <Input placeholder="Например: AWS, Microsoft" />
        </Form.Item>

        <Form.Item
          name="comment"
          label="Описание (опционально)"
        >
          <TextArea
            rows={2}
            placeholder="Краткое описание расхода"
            maxLength={500}
          />
        </Form.Item>
      </Form>

      <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f0f5ff', borderRadius: 6 }}>
        <p style={{ margin: 0, fontSize: 12, color: '#666' }}>
          <strong>Обязательные поля:</strong> Дата, Статья, Сумма
          <br />
          Расход будет добавлен в выбранный месяц и учтён в остатках.
        </p>
      </div>
    </Modal>
  )
}

export default QuickExpenseModal
