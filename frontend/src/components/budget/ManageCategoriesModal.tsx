/**
 * Manage Categories Modal
 * Allows adding/removing categories from budget version and creating new categories
 */
import React, { useState, useMemo } from 'react'
import { Modal, Transfer, message, Alert, Space, Typography, Button, Form, Input, Select, Divider, Spin } from 'antd'
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
  versionId: number
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
  versionId,
  categories,
  planDetails,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient()
  const [removing, setRemoving] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm] = Form.useForm()
  const [freshPlanDetails, setFreshPlanDetails] = useState<BudgetPlanDetail[]>([])
  const [loadingFreshData, setLoadingFreshData] = useState(false)

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

  // Load fresh plan details when modal opens
  React.useEffect(() => {
    if (open) {
      const loadFreshData = async () => {
        setLoadingFreshData(true)
        try {
          const data = await planDetailsApi.getByVersion(versionId)
          setFreshPlanDetails(data)
        } catch (error) {
          console.error('Failed to load plan details:', error)
          setFreshPlanDetails(planDetails)
        } finally {
          setLoadingFreshData(false)
        }
      }
      loadFreshData()
    }
  }, [open, versionId, planDetails])

  // Get categories that have plan details (use fresh data)
  const usedCategoryIds = useMemo(() => {
    return new Set(freshPlanDetails.map(pd => pd.category_id))
  }, [freshPlanDetails])

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
  const [targetKeys, setTargetKeys] = useState<Key[]>([])

  // Sync targetKeys only when modal opens
  React.useEffect(() => {
    if (open) {
      const newTargetKeys = leafCategories
        .filter(cat => usedCategoryIds.has(cat.id))
        .map(cat => cat.id.toString())
      setTargetKeys(newTargetKeys)
    }
  }, [open, leafCategories, usedCategoryIds])

  const handleChange = (newTargetKeys: Key[]) => {
    setTargetKeys(newTargetKeys)
  }

  const handleRemoveCategories = async (categoryIdsToRemove: number[]) => {
    setRemoving(true)

    try {
      // Get latest plan details from server to ensure we have all records
      const latestPlanDetails = await planDetailsApi.getByVersion(versionId)

      // Find all plan details for these categories
      const detailsToRemove = latestPlanDetails.filter(pd =>
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

      // Invalidate plan details cache to refetch updated data
      // Use the correct queryKey pattern from budgetPlanningKeys
      queryClient.invalidateQueries({ queryKey: ['budgetPlanning', 'planDetails'] })

      message.success(`Удалено ${detailsToRemove.length} записей`)
      onSuccess()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при удалении категорий')
      console.error('Remove categories error:', error)
    } finally {
      setRemoving(false)
    }
  }

  const handleAddCategories = async (categoryIdsToAdd: number[]) => {
    setRemoving(true)

    try {
      // Create one empty plan detail (month 1) for each category to make it appear in table
      // Other months will be created when user enters values
      const promises = categoryIdsToAdd.map(categoryId => {
        const category = categories.find(c => c.id === categoryId)
        if (!category) {
          throw new Error(`Category with id ${categoryId} not found`)
        }
        return planDetailsApi.create({
          version_id: versionId,
          category_id: categoryId,
          month: 1,
          planned_amount: 0,
          type: category.type,
        })
      })

      await Promise.all(promises)

      // Invalidate plan details cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['budgetPlanning', 'planDetails'] })

      message.success(`Добавлено ${categoryIdsToAdd.length} категорий`)
      onSuccess()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при добавлении категорий')
      console.error('Add categories error:', error)
    } finally {
      setRemoving(false)
    }
  }

  const handleSave = async () => {
    const currentCategoryIds = new Set(usedCategoryIds)
    const newCategoryIds = new Set(targetKeys.map(key => Number(key.toString())))

    // Find categories to remove and add
    const toRemove = Array.from(currentCategoryIds).filter(id => !newCategoryIds.has(id))
    const toAdd = Array.from(newCategoryIds).filter(id => !currentCategoryIds.has(id))

    if (toRemove.length > 0 && toAdd.length > 0) {
      // Both adding and removing
      Modal.confirm({
        title: 'Применить изменения?',
        content: `Будет добавлено ${toAdd.length} категорий и удалено ${toRemove.length} категорий. Продолжить?`,
        okText: 'Применить',
        cancelText: 'Отмена',
        onOk: async () => {
          await handleRemoveCategories(toRemove)
          await handleAddCategories(toAdd)
          onClose()
        },
      })
    } else if (toRemove.length > 0) {
      // Only removing
      Modal.confirm({
        title: 'Удалить категории?',
        content: `Будут удалены все данные для ${toRemove.length} категорий. Продолжить?`,
        okText: 'Удалить',
        cancelText: 'Отмена',
        okButtonProps: { danger: true },
        onOk: async () => {
          await handleRemoveCategories(toRemove)
          onClose()
        },
      })
    } else if (toAdd.length > 0) {
      // Only adding
      await handleAddCategories(toAdd)
      onClose()
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

        <Spin spinning={loadingFreshData} tip="Загрузка категорий...">
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
        </Spin>

        <div style={{ padding: '12px 16px', backgroundColor: '#fff7e6', borderRadius: 4 }}>
          <Text strong>
            Категорий в версии: {targetKeys.length} из {leafCategories.length}
          </Text>
        </div>
      </Space>
    </Modal>
  )
}
