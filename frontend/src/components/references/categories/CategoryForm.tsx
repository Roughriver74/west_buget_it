import React from 'react'
import { Form, Input, Radio, Checkbox, Select, FormInstance } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import type { BudgetCategory } from '@/types'

const { TextArea } = Input
const { Option } = Select

interface CategoryFormProps {
  form?: FormInstance
  initialValues?: Partial<BudgetCategory>
  onFinish: (values: any) => void
  currentCategoryId?: number
}

const CategoryForm: React.FC<CategoryFormProps> = ({ form, initialValues, onFinish, currentCategoryId }) => {
  // Загружаем все активные категории для выбора родителя
  const { data: categories } = useQuery({
    queryKey: ['categories', { is_active: true }],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  // Фильтруем категории: исключаем текущую категорию (чтобы не создать циклическую ссылку)
  const availableParents = categories?.filter(cat => cat.id !== currentCategoryId) || []

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        is_active: true,
        parent_id: null,
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
        name="parent_id"
        label="Родительская категория"
        tooltip="Выберите, если это подкатегория другой статьи расходов"
      >
        <Select
          placeholder="Корневая категория (не выбрано)"
          allowClear
          showSearch
          optionFilterProp="children"
        >
          {availableParents.map((cat) => (
            <Option key={cat.id} value={cat.id}>
              {cat.name} ({cat.type})
            </Option>
          ))}
        </Select>
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
