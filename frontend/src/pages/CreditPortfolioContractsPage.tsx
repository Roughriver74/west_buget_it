import { useState, useMemo, useEffect } from 'react'
import { Card, Tag, Button, Space, Input, Empty, Spin, Pagination, Row, Col } from 'antd'
import { SearchOutlined, FileTextOutlined, DollarOutlined, ReloadOutlined, CalendarOutlined, BankOutlined } from '@ant-design/icons'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import type { FinContract } from '@/api/creditPortfolio'
import dayjs from 'dayjs'
import CreditPortfolioFilters, {
  type CreditPortfolioFilterValues,
} from '@/components/bank/CreditPortfolioFilters'

const { Search } = Input

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

const PAGE_SIZE = 20

// Format number to millions/billions
const formatAmount = (value: number): string => {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} млрд`
  } else if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)} млн`
  } else if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)} тыс`
  }
  return value.toLocaleString('ru-RU')
}

export default function CreditPortfolioContractsPage() {
  const { selectedDepartment } = useDepartment()
  const [searchText, setSearchText] = useState('')
  const [filters, setFilters] = useState<CreditPortfolioFilterValues>({})
  const [currentPage, setCurrentPage] = useState(1)

  // Debounce search
  const debouncedSearch = useDebounce(searchText, 300)

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [debouncedSearch, filters])

  const { data: contracts, isLoading, isError, refetch } = useQuery({
    queryKey: ['credit-contracts', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getContracts({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000,
  })

  // Filter contracts by search text
  const filteredContracts = useMemo(() => {
    if (!contracts) return []

    let filtered = contracts

    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase()
      filtered = contracts.filter((contract: FinContract) =>
        contract.contract_number.toLowerCase().includes(searchLower) ||
        contract.counterparty?.toLowerCase().includes(searchLower)
      )
    }

    return filtered
  }, [contracts, debouncedSearch])

  // Paginate data
  const paginatedContracts = useMemo(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE
    return filteredContracts.slice(startIndex, startIndex + PAGE_SIZE)
  }, [filteredContracts, currentPage])

  // Calculate total sum for current page
  const currentPageTotal = useMemo(() => {
    return paginatedContracts.reduce((sum: number, contract: FinContract) => {
      // Explicitly convert to numbers to avoid string concatenation
      const totalPaid = Number(contract.total_paid) || 0
      const principal = Number(contract.principal) || 0
      const interest = Number(contract.interest) || 0
      const total = totalPaid || (principal + interest)
      return sum + total
    }, 0)
  }, [paginatedContracts])

  // Loading state
  if (isLoading && !contracts) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: 24
      }}>
        <Spin size="large" />
        <p style={{ marginTop: 16, color: '#8c8c8c' }}>Загрузка договоров...</p>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: 24,
        gap: 16
      }}>
        <p style={{ color: '#8c8c8c', textAlign: 'center' }}>
          Не удалось загрузить договоры. Попробуйте еще раз.
        </p>
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={() => refetch()}
        >
          Обновить
        </Button>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      {/* Filters */}
      <CreditPortfolioFilters
        onFilterChange={setFilters}
        initialValues={filters}
      />

      {/* Title */}
      <h1 style={{ margin: '24px 0 16px 0', fontSize: 28, fontWeight: 600 }}>
        Управление договорами
      </h1>
      <p style={{ margin: '0 0 24px 0', color: '#8c8c8c' }}>
        Детальная информация по кредитным договорам
      </p>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={12} lg={8}>
          <Card
            bordered={false}
            style={{
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
            }}
          >
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <FileTextOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <span style={{ fontSize: 14, color: '#8c8c8c' }}>Всего договоров</span>
              </div>
              <div style={{ fontSize: 32, fontWeight: 600 }}>
                {filteredContracts.length}
              </div>
              <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                Уникальные кредитные договоры (contract_number) с учетом фильтров
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={12} lg={8}>
          <Card
            bordered={false}
            style={{
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              borderLeft: '4px solid #52c41a'
            }}
          >
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <DollarOutlined style={{ fontSize: 20, color: '#52c41a' }} />
                <span style={{ fontSize: 14, color: '#8c8c8c' }}>Сумма на странице</span>
              </div>
              <div style={{ fontSize: 32, fontWeight: 600, color: '#52c41a' }}>
                {formatAmount(currentPageTotal)}
              </div>
              <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                Сумма всех платежей по договорам на текущей странице ({paginatedContracts.length} из {filteredContracts.length})
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Search */}
      <Card
        bordered={false}
        style={{
          marginBottom: 16,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}
      >
        <Search
          placeholder="Поиск по номеру договора или организации..."
          allowClear
          size="large"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          prefix={<SearchOutlined />}
          style={{ maxWidth: 600 }}
        />
      </Card>

      {/* Contracts Cards */}
      {filteredContracts.length === 0 ? (
        <Card
          bordered={false}
          style={{
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}
        >
          <Empty
            description={
              debouncedSearch
                ? 'Договоры не найдены по заданным фильтрам'
                : 'Договоры не найдены'
            }
          />
        </Card>
      ) : (
        <>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            {paginatedContracts.map((contract: FinContract) => (
              <Card
                key={contract.id}
                bordered={false}
                hoverable
                style={{
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  transition: 'all 0.3s ease'
                }}
                bodyStyle={{ padding: 20 }}
              >
                <Row gutter={16} align="middle">
                  {/* Left: Contract Info */}
                  <Col xs={24} sm={12} md={8}>
                    <Space direction="vertical" size={4}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileTextOutlined style={{ fontSize: 18, color: '#1890ff' }} />
                        <span style={{ fontSize: 16, fontWeight: 600 }}>
                          {contract.contract_number}
                          {contract.contract_date && (
                            <span style={{ fontWeight: 400, color: '#8c8c8c', marginLeft: 4 }}>
                              от {dayjs(contract.contract_date).format('DD.MM.YYYY')}
                            </span>
                          )}
                        </span>
                      </div>
                      {contract.counterparty && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                          <BankOutlined style={{ fontSize: 14, color: '#8c8c8c' }} />
                          <span style={{ fontSize: 14, color: '#595959' }}>{contract.counterparty}</span>
                        </div>
                      )}
                      {contract.contract_type && (
                        <Tag color={contract.contract_type === 'Кредит' ? 'blue' : 'green'} style={{ marginTop: 4 }}>
                          {contract.contract_type}
                        </Tag>
                      )}
                    </Space>
                  </Col>

                  {/* Center: Additional Info */}
                  <Col xs={24} sm={12} md={6}>
                    <Space direction="vertical" size={2}>
                      <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                        <CalendarOutlined style={{ marginRight: 4 }} />
                        Последний платеж: —
                      </div>
                      <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                        Операций: —
                      </div>
                    </Space>
                  </Col>

                  {/* Right: Amounts */}
                  <Col xs={24} sm={24} md={10}>
                    <Row gutter={16} style={{ textAlign: 'right' }}>
                      <Col span={8}>
                        <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
                          Всего выплачено
                        </div>
                        <div style={{ fontSize: 18, fontWeight: 600 }}>
                          {contract.total_paid != null && Number(contract.total_paid) !== 0
                            ? formatAmount(Number(contract.total_paid))
                            : '—'}
                        </div>
                      </Col>
                      <Col span={8}>
                        <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
                          Тело
                        </div>
                        <div style={{ fontSize: 18, fontWeight: 600, color: '#52c41a' }}>
                          {contract.principal != null && Number(contract.principal) !== 0
                            ? formatAmount(Number(contract.principal))
                            : '—'}
                        </div>
                      </Col>
                      <Col span={8}>
                        <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
                          Проценты
                        </div>
                        <div style={{ fontSize: 18, fontWeight: 600, color: '#fa8c16' }}>
                          {contract.interest != null && Number(contract.interest) !== 0
                            ? formatAmount(Number(contract.interest))
                            : '—'}
                        </div>
                      </Col>
                    </Row>
                  </Col>
                </Row>
              </Card>
            ))}
          </Space>

          {/* Pagination */}
          {filteredContracts.length > PAGE_SIZE && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              marginTop: 24,
              padding: '16px 0'
            }}>
              <Pagination
                current={currentPage}
                pageSize={PAGE_SIZE}
                total={filteredContracts.length}
                onChange={setCurrentPage}
                showSizeChanger={false}
                showTotal={(total, range) =>
                  `${range[0]}-${range[1]} из ${total} договоров`
                }
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
