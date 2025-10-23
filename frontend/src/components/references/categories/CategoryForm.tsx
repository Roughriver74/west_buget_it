import React from 'react'
import { Form, Input, Radio, Checkbox, FormInstance } from 'antd'
import type { BudgetCategory, ExpenseType } from '@/types'

const { TextArea } = Input

interface CategoryFormProps {
  form?: FormInstance
  initialValues?: Partial<BudgetCategory>
  onFinish: (values: any) => void
}

const CategoryForm: React.FC<CategoryFormProps> = ({ form, initialValues, onFinish }) => {
  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        is_active: true,
        ...initialValues,
      }}
      onFinish={onFinish}
    >
      <Form.Item
        name="name"
        label="Название статьи"
        rules={[
          { required: true, message: 'Введите название статьи' },
          { max: 255, message: 'Максимум 255 символов' },
        ]}
      >
        <Input placeholder="Например: Серверы и хостинг" />
      </Form.Item>

      <Form.Item
        name="type"
        label="Тип расходов"
        rules={[{ required: true, message: 'Выберите тип расходов' }]}
      >
        <Radio.Group>
          <Radio value="OPEX">OPEX (Операционные расходы)</Radio>
          <Radio value="CAPEX">CAPEX (Капитальные расходы)</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        name="description"
        label="Описание"
      >
        <TextArea
          rows={3}
          placeholder="Опциональное описание статьи расходов"
          maxLength={1000}
          showCount
        />
      </Form.Item>

      <Form.Item
        name="is_active"
        valuePropName="checked"
      >
        <Checkbox>Активна</Checkbox>
      </Form.Item>
    </Form>
  )
}

export default CategoryForm
