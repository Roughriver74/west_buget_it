/**
 * Manage Categories Modal
 * Allows adding/removing categories from budget version
 */
import React, { useState, useMemo } from 'react'
import { Modal, Transfer, message, Alert, Space, Typography } from 'antd'
import type { Key } from 'react'
import { planDetailsApi } from '@/api/budgetPlanning'
import type { BudgetPlanDetail } from '@/types/budgetPlanning'
import { ExpenseType } from '@/types/budgetPlanning'

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
  const [removing, setRemoving] = useState(false)

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
        },
      })
    } else {
      message.info('Нет изменений')
      onClose()
    }
  }

  const handleClose = () => {
    // Reset to original state
    setTargetKeys(
      leafCategories
        .filter(cat => usedCategoryIds.has(cat.id))
        .map(cat => cat.id.toString())
    )
    onClose()
  }

  return (
    <Modal
      open={open}
      title="Управление категориями"
      width={800}
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
