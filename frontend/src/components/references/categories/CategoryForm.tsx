import React from 'react'
import { Form, Input, Radio, Checkbox, Select, FormInstance } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { categoriesApi, departmentsApi } from '@/api'
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'
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
  const { user } = useAuth()
  const { selectedDepartment } = useDepartment()

  // Загружаем все активные категории для выбора родителя
  const { data: categories } = useQuery({
    queryKey: ['categories', { is_active: true }],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  // Загружаем отделы для ADMIN/MANAGER
  const { data: departments } = useQuery({
    queryKey: ['departments', { is_active: true }],
    queryFn: () => departmentsApi.getAll({ is_active: true }),
    enabled: user?.role === 'ADMIN' || user?.role === 'MANAGER',
  })

  // Фильтруем категории: исключаем текущую категорию (чтобы не создать циклическую ссылку)
  const availableParents = categories?.filter(cat => cat.id !== currentCategoryId) || []

  // Показываем поле department_id только для ADMIN/MANAGER
  const canSelectDepartment = user?.role === 'ADMIN' || user?.role === 'MANAGER'

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        is_active: true,
        parent_id: null,
        department_id: selectedDepartment?.id || user?.department_id,
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

      {canSelectDepartment && (
        <Form.Item
          name="department_id"
          label="Отдел"
          rules={[{ required: true, message: 'Выберите отдел' }]}
          tooltip="Статья будет привязана к выбранному отделу"
        >
          <Select
            placeholder="Выберите отдел"
            showSearch
            optionFilterProp="children"
          >
            {departments?.map((dept) => (
              <Option key={dept.id} value={dept.id}>
                {dept.name}
              </Option>
            ))}
          </Select>
        </Form.Item>
      )}

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
