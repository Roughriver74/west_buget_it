/**
 * Manage Categories Modal
 * Allows adding/removing categories from budget version and creating new categories
 */
import React, { useState, useMemo } from 'react'
import { Modal, Transfer, message, Alert, Space, Typography, Button, Form, Input, Select, Divider } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import type { Key } from 'react'
import { planDetailsApi } from '@/api/budgetPlanning'
import type { BudgetPlanDetail } from '@/types/budgetPlanning'
import { ExpenseType } from '@/types/budgetPlanning'
import { categoriesApi } from '@/api/categories'
import { useMutation, useQueryClient } from '@tanstack/react-query'

const { Text } = Typography

interface Category {
  id: number
  name: string
  type: ExpenseType
  parentId: number | null
}

interface ManageCategoriesModalProps {
  open: boolean
  categories: Category[]
  planDetails: BudgetPlanDetail[]
  onClose: () => void
  onSuccess: () => void
}

interface TransferItem {
  key: string
  title: string
  description: string
  disabled?: boolean
}

export const ManageCategoriesModal: React.FC<ManageCategoriesModalProps> = ({
  open,
  categories,
  planDetails,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient()
  const [removing, setRemoving] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm] = Form.useForm()

  // Create category mutation
  const createCategoryMutation = useMutation({
    mutationFn: (data: { name: string; type: ExpenseType; parent_id?: number | null }) =>
      categoriesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Категория создана')
      createForm.resetFields()
      setShowCreateForm(false)
      onSuccess()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании категории')
    },
  })

  // Get categories that have plan details
  const usedCategoryIds = useMemo(() => {
    return new Set(planDetails.map(pd => pd.category_id))
  }, [planDetails])

  // Filter only leaf categories (categories without children)
  const leafCategories = useMemo(() => {
    return categories.filter(cat => {
      const hasChildren = categories.some(c => c.parentId === cat.id)
      return !hasChildren
    })
  }, [categories])

  // Prepare data for Transfer component
  const transferData: TransferItem[] = useMemo(() => {
    return leafCategories.map(cat => ({
      key: cat.id.toString(),
      title: cat.name,
      description: cat.type,
      disabled: false,
    }))
  }, [leafCategories])

  // Target keys (categories that are currently in the version)
  const [targetKeys, setTargetKeys] = useState<Key[]>(() => {
    return leafCategories
      .filter(cat => usedCategoryIds.has(cat.id))
      .map(cat => cat.id.toString())
  })

  const handleChange = (newTargetKeys: Key[]) => {
    setTargetKeys(newTargetKeys)
  }

  const handleRemoveCategories = async (categoryIdsToRemove: number[]) => {
    setRemoving(true)

    try {
      // Find all plan details for these categories
      const detailsToRemove = planDetails.filter(pd =>
        categoryIdsToRemove.includes(pd.category_id)
      )

      if (detailsToRemove.length === 0) {
        message.info('Нет данных для удаления')
        return
      }

      // Delete all plan details for removed categories
      const promises = detailsToRemove.map(detail =>
        planDetailsApi.delete(detail.id)
      )

      await Promise.all(promises)

      message.success(`Удалено ${detailsToRemove.length} записей`)
      onSuccess()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при удалении категорий')
      console.error('Remove categories error:', error)
    } finally {
      setRemoving(false)
    }
  }

  const handleSave = async () => {
    const currentCategoryIds = new Set(usedCategoryIds)
    const newCategoryIds = new Set(targetKeys.map(key => Number(key.toString())))

    // Find categories to remove
    const toRemove = Array.from(currentCategoryIds).filter(id => !newCategoryIds.has(id))

    if (toRemove.length > 0) {
      // Show confirmation if removing categories with data
      Modal.confirm({
        title: 'Удалить категории?',
        content: `Будут удалены все данные для ${toRemove.length} категорий. Продолжить?`,
        okText: 'Удалить',
        cancelText: 'Отмена',
        okButtonProps: { danger: true },
        onOk: async () => {
          await handleRemoveCategories(toRemove)
          onClose() // Закрываем модальное окно после успешного удаления
        },
      })
    } else {
      message.info('Нет изменений')
      onClose()
    }
  }

  const handleCreateCategory = async () => {
    try {
      const values = await createForm.validateFields()
      await createCategoryMutation.mutateAsync({
        name: values.name,
        type: values.type,
        parent_id: values.parent_id || null,
      })
    } catch (error) {
      console.error('Create category error:', error)
    }
  }

  const handleClose = () => {
    // Reset to original state
    setTargetKeys(
      leafCategories
        .filter(cat => usedCategoryIds.has(cat.id))
        .map(cat => cat.id.toString())
    )
    setShowCreateForm(false)
    createForm.resetFields()
    onClose()
  }

  // Get parent category options (only parent categories can be selected as parents)
  const parentCategoryOptions = useMemo(() => {
    return categories
      .filter(cat => {
        const hasChildren = categories.some(c => c.parentId === cat.id)
        return hasChildren || cat.parentId === null
      })
      .map(cat => ({
        label: cat.name,
        value: cat.id,
      }))
  }, [categories])

  return (
    <Modal
      open={open}
      title="Управление категориями"
      width={900}
      onCancel={handleClose}
      onOk={handleSave}
      confirmLoading={removing}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Alert
          message="Управление категориями в версии"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Переместите категории между списками</li>
              <li>Левая панель: доступные категории</li>
              <li>Правая панель: категории в версии бюджета</li>
              <li>При удалении категории удаляются все её данные</li>
            </ul>
          }
          type="info"
          showIcon
        />

        {/* Create Category Section */}
        <div>
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateForm(!showCreateForm)}
            style={{ width: '100%' }}
          >
            {showCreateForm ? 'Скрыть форму создания' : 'Создать новую категорию'}
          </Button>

          {showCreateForm && (
            <div style={{ marginTop: 16, padding: 16, border: '1px solid #d9d9d9', borderRadius: 4 }}>
              <Form
                form={createForm}
                layout="vertical"
                onFinish={handleCreateCategory}
              >
                <Form.Item
                  name="name"
                  label="Название категории"
                  rules={[{ required: true, message: 'Введите название категории' }]}
                >
                  <Input placeholder="Например: Облачные сервисы" />
                </Form.Item>

                <Form.Item
                  name="type"
                  label="Тип расходов"
                  rules={[{ required: true, message: 'Выберите тип расходов' }]}
                >
                  <Select placeholder="Выберите тип">
                    <Select.Option value={ExpenseType.OPEX}>OPEX (Операционные расходы)</Select.Option>
                    <Select.Option value={ExpenseType.CAPEX}>CAPEX (Капитальные расходы)</Select.Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="parent_id"
                  label="Родительская категория (опционально)"
                >
                  <Select
                    placeholder="Выберите родительскую категорию или оставьте пустым"
                    allowClear
                    options={parentCategoryOptions}
                  />
                </Form.Item>

                <Form.Item style={{ marginBottom: 0 }}>
                  <Space>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={createCategoryMutation.isPending}
                    >
                      Создать категорию
                    </Button>
                    <Button
                      onClick={() => {
                        setShowCreateForm(false)
                        createForm.resetFields()
                      }}
                    >
                      Отмена
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
          )}
        </div>

        <Divider />

        <Transfer
          dataSource={transferData}
          titles={['Доступные категории', 'В версии']}
          targetKeys={targetKeys}
          onChange={handleChange}
          render={item => (
            <div>
              <div>{item.title}</div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {item.description}
              </Text>
            </div>
          )}
          listStyle={{
            width: 350,
            height: 400,
          }}
          operations={['Добавить', 'Удалить']}
          locale={{
            itemUnit: 'категория',
            itemsUnit: 'категории',
            notFoundContent: 'Нет данных',
            searchPlaceholder: 'Поиск категорий',
          }}
          showSearch
          filterOption={(inputValue, item) =>
            item.title.toLowerCase().includes(inputValue.toLowerCase())
          }
        />

        <div style={{ padding: '12px 16px', backgroundColor: '#fff7e6', borderRadius: 4 }}>
          <Text strong>
            Категорий в версии: {targetKeys.length} из {leafCategories.length}
          </Text>
        </div>
      </Space>
    </Modal>
  )
}
