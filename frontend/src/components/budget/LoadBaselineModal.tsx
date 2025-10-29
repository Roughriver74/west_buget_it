/**
 * Load Baseline Modal
 * Allows loading previous year data into budget plan
 */
import React, { useState, useMemo, useCallback } from 'react'
import { Modal, Checkbox, Table, message, Button, Space, Typography, Alert, Spin } from 'antd'
import { DownloadOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { calculatorApi, planDetailsApi } from '@/api/budgetPlanning'
import type { BaselineSummary, BudgetPlanDetailCreate } from '@/types/budgetPlanning'
import { ExpenseType, CalculationMethod } from '@/types/budgetPlanning'

const { Text } = Typography

interface Category {
  id: number
  name: string
  type: ExpenseType
  parentId: number | null
}

interface LoadBaselineModalProps {
  open: boolean
  versionId: number
  year: number
  categories: Category[]
  onClose: () => void
  onSuccess: () => void
}

interface CategoryWithBaseline extends Category {
  baseline?: BaselineSummary
  loading?: boolean
  error?: string
}

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

export const LoadBaselineModal: React.FC<LoadBaselineModalProps> = ({
  open,
  versionId,
  year,
  categories,
  onClose,
  onSuccess,
}) => {
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<number>>(new Set())
  const [categoriesData, setCategoriesData] = useState<Map<number, CategoryWithBaseline>>(new Map())
  const [loadingBaseline, setLoadingBaseline] = useState(false)
  const [applying, setApplying] = useState(false)

  const previousYear = year - 1

  // Filter only leaf categories (no children)
  const leafCategories = useMemo(() => {
    return categories.filter(c => {
      // Category is a leaf if it has no children
      const hasChildren = categories.some(other => other.parentId === c.id)
      return !hasChildren
    })
  }, [categories])

  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      setSelectedCategoryIds(new Set(leafCategories.map(c => c.id)))
    } else {
      setSelectedCategoryIds(new Set())
    }
  }, [leafCategories])

  const handleSelectCategory = useCallback((categoryId: number, checked: boolean) => {
    setSelectedCategoryIds(prev => {
      const next = new Set(prev)
      if (checked) {
        next.add(categoryId)
      } else {
        next.delete(categoryId)
      }
      return next
    })
  }, [])

  const handleLoadBaseline = async () => {
    if (selectedCategoryIds.size === 0) {
      message.warning('Выберите хотя бы одну категорию')
      return
    }

    setLoadingBaseline(true)

    try {
      const updates = new Map(categoriesData)

      // Load baseline for selected categories
      const promises = Array.from(selectedCategoryIds).map(async (categoryId) => {
        try {
          updates.set(categoryId, {
            ...leafCategories.find(c => c.id === categoryId)!,
            loading: true,
          })
          setCategoriesData(new Map(updates))

          const baseline = await calculatorApi.getBaseline(categoryId, previousYear)

          updates.set(categoryId, {
            ...leafCategories.find(c => c.id === categoryId)!,
            baseline,
            loading: false,
          })
          setCategoriesData(new Map(updates))
        } catch (error: any) {
          console.error(`Failed to load baseline for category ${categoryId}:`, error)
          updates.set(categoryId, {
            ...leafCategories.find(c => c.id === categoryId)!,
            loading: false,
            error: error.response?.data?.detail || 'Ошибка загрузки',
          })
          setCategoriesData(new Map(updates))
        }
      })

      await Promise.all(promises)
      message.success(`Загружены данные за ${previousYear} год`)
    } catch (error) {
      message.error('Ошибка при загрузке данных')
      console.error('Baseline load error:', error)
    } finally {
      setLoadingBaseline(false)
    }
  }

  const handleApply = async () => {
    const categoriesToApply = Array.from(selectedCategoryIds)
      .map(id => categoriesData.get(id))
      .filter(c => c && c.baseline)

    if (categoriesToApply.length === 0) {
      message.warning('Нет данных для применения. Сначала загрузите baseline данные.')
      return
    }

    setApplying(true)

    try {
      const creations: BudgetPlanDetailCreate[] = []

      // Create plan details for each month of each category
      for (const categoryData of categoriesToApply) {
        if (!categoryData || !categoryData.baseline) continue

        const { baseline } = categoryData

        // Create plan detail for each month
        baseline.monthly_breakdown.forEach((monthData) => {
          creations.push({
            version_id: versionId,
            category_id: baseline.category_id,
            month: monthData.month,
            planned_amount: Number(monthData.amount || 0),
            type: categoryData.type,
            calculation_method: CalculationMethod.MANUAL,
            based_on_year: previousYear,
          })
        })
      }

      // Create all plan details
      const promises = creations.map(data => planDetailsApi.create(data))
      await Promise.all(promises)

      message.success(`Применено данных для ${categoriesToApply.length} категорий`)
      onSuccess()
      handleClose()
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при применении данных')
      console.error('Apply baseline error:', error)
    } finally {
      setApplying(false)
    }
  }

  const handleClose = () => {
    setSelectedCategoryIds(new Set())
    setCategoriesData(new Map())
    onClose()
  }

  const columns: ColumnsType<Category> = [
    {
      title: (
        <Checkbox
          checked={selectedCategoryIds.size === leafCategories.length && leafCategories.length > 0}
          indeterminate={selectedCategoryIds.size > 0 && selectedCategoryIds.size < leafCategories.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
        >
          Категория
        </Checkbox>
      ),
      key: 'category',
      render: (_, record) => {
        const categoryData = categoriesData.get(record.id)
        return (
          <Space>
            <Checkbox
              checked={selectedCategoryIds.has(record.id)}
              onChange={(e) => handleSelectCategory(record.id, e.target.checked)}
            />
            <div>
              <div>{record.name}</div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.type}
              </Text>
            </div>
            {categoryData?.loading && <Spin size="small" />}
            {categoryData?.baseline && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
          </Space>
        )
      },
    },
    {
      title: `Сумма ${previousYear} г.`,
      key: 'total',
      align: 'right',
      render: (_, record) => {
        const categoryData = categoriesData.get(record.id)
        if (!categoryData?.baseline) {
          return <Text type="secondary">—</Text>
        }
        if (categoryData.error) {
          return <Text type="danger">Ошибка</Text>
        }
        return <Text strong>{currencyFormatter.format(Number(categoryData.baseline.total_amount || 0))}</Text>
      },
    },
    {
      title: 'Средняя в месяц',
      key: 'avg',
      align: 'right',
      render: (_, record) => {
        const categoryData = categoriesData.get(record.id)
        if (!categoryData?.baseline) {
          return <Text type="secondary">—</Text>
        }
        return <Text>{currencyFormatter.format(Number(categoryData.baseline.monthly_avg || 0))}</Text>
      },
    },
  ]

  const totalSelected = useMemo(() => {
    let sum = 0
    selectedCategoryIds.forEach(id => {
      const categoryData = categoriesData.get(id)
      if (categoryData?.baseline) {
        sum += Number(categoryData.baseline.total_amount || 0)
      }
    })
    return sum
  }, [selectedCategoryIds, categoriesData])

  return (
    <Modal
      open={open}
      title={`Загрузить данные из ${previousYear} года`}
      width={800}
      onCancel={handleClose}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          Отмена
        </Button>,
        <Button
          key="load"
          icon={<DownloadOutlined />}
          onClick={handleLoadBaseline}
          loading={loadingBaseline}
          disabled={selectedCategoryIds.size === 0}
        >
          Загрузить данные
        </Button>,
        <Button
          key="apply"
          type="primary"
          onClick={handleApply}
          loading={applying}
          disabled={selectedCategoryIds.size === 0 || Array.from(selectedCategoryIds).every(id => !categoriesData.get(id)?.baseline)}
        >
          Применить к версии
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Alert
          message="Как использовать"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Выберите категории для загрузки</li>
              <li>Нажмите "Загрузить данные" для получения данных за {previousYear} год</li>
              <li>Проверьте суммы и нажмите "Применить к версии"</li>
            </ul>
          }
          type="info"
          showIcon
        />

        <Table
          columns={columns}
          dataSource={leafCategories}
          rowKey="id"
          pagination={false}
          size="small"
          scroll={{ y: 400 }}
        />

        {selectedCategoryIds.size > 0 && (
          <div style={{ padding: '12px 16px', backgroundColor: '#f0f5ff', borderRadius: 4 }}>
            <Space direction="vertical" size="small">
              <Text>
                <strong>Выбрано категорий:</strong> {selectedCategoryIds.size}
              </Text>
              {totalSelected > 0 && (
                <Text>
                  <strong>Общая сумма:</strong> {currencyFormatter.format(totalSelected)}
                </Text>
              )}
            </Space>
          </div>
        )}
      </Space>
    </Modal>
  )
}
