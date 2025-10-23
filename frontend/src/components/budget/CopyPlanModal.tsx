import React, { useState } from 'react'
import { Modal, Form, InputNumber, Select, message } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { budgetApi } from '@/api'

const { Option } = Select

interface CopyPlanModalProps {
  open: boolean
  targetYear: number
  onClose: () => void
  onSuccess: () => void
}

const CopyPlanModal: React.FC<CopyPlanModalProps> = ({ open, targetYear, onClose, onSuccess }) => {
  const [form] = Form.useForm()

  const copyMutation = useMutation({
    mutationFn: ({ sourceYear, coefficient }: { sourceYear: number; coefficient: number }) =>
      budgetApi.copyPlan(targetYear, sourceYear, coefficient),
    onSuccess: (data) => {
      message.success(`План скопирован! Создано: ${data.created_entries}, обновлено: ${data.updated_entries}`)
      onSuccess()
      onClose()
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка копирования: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (values: any) => {
    copyMutation.mutate({
      sourceYear: values.sourceYear,
      coefficient: values.coefficient,
    })
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  // Генерируем список последних 10 лет
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 10 }, (_, i) => currentYear - i + 1).filter((y) => y !== targetYear)

  return (
    <Modal
      title={`Скопировать план в ${targetYear} год`}
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={copyMutation.isPending}
      width={500}
      okText="Скопировать"
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          sourceYear: targetYear - 1,
          coefficient: 1.0,
        }}
      >
        <Form.Item
          name="sourceYear"
          label="Исходный год"
          rules={[{ required: true, message: 'Выберите исходный год' }]}
        >
          <Select placeholder="Выберите год">
            {years.map((year) => (
              <Option key={year} value={year}>
                {year} год
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="coefficient"
          label="Коэффициент корректировки"
          rules={[{ required: true, message: 'Введите коэффициент' }]}
          extra="1.0 = без изменений, 1.1 = +10%, 0.9 = -10%"
        >
          <InputNumber
            min={0.1}
            max={10}
            step={0.1}
            style={{ width: '100%' }}
            placeholder="Например: 1.1"
          />
        </Form.Item>

        <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f5ff', borderRadius: 6 }}>
          <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
            <strong>Как это работает:</strong>
            <br />
            Все суммы из выбранного года будут скопированы в {targetYear} год и умножены на коэффициент.
            <br />
            Например, если план на январь был 100 000 ₽, а коэффициент 1.1, то новая сумма будет 110 000 ₽.
          </p>
        </div>
      </Form>
    </Modal>
  )
}

export default CopyPlanModal
