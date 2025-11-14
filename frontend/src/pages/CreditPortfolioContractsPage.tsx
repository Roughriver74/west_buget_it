import { useState, useMemo, useEffect } from 'react'
import { Card, Table, Tag, Button, Space, Input, Select, Empty, Spin, Statistic, Pagination, Row, Col } from 'antd'
import { SearchOutlined, FilterOutlined, FileTextOutlined, DollarOutlined, ReloadOutlined } from '@ant-design/icons'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import type { FinContract } from '@/api/creditPortfolio'
import dayjs from 'dayjs'

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

export default function CreditPortfolioContractsPage() {
  const { selectedDepartment } = useDepartment()
  const [searchText, setSearchText] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)
  const [filterType, setFilterType] = useState<string | undefined>(undefined)
  const [currentPage, setCurrentPage] = useState(1)

  // Debounce search and filters
  const debouncedSearch = useDebounce(searchText, 300)
  const debouncedFilterActive = useDebounce(filterActive, 300)
  const debouncedFilterType = useDebounce(filterType, 300)

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [debouncedSearch, debouncedFilterActive, debouncedFilterType])

  const { data: contracts, isLoading, isError, refetch } = useQuery({
    queryKey: ['credit-contracts', selectedDepartment?.id, debouncedFilterActive, debouncedFilterType],
    queryFn: () =>
      creditPortfolioApi.getContracts({
        department_id: selectedDepartment?.id,
        is_active: debouncedFilterActive,
        contract_type: debouncedFilterType,
      }),
    enabled: !!selectedDepartment,
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  })

  const { data: contractStats } = useQuery({
    queryKey: ['credit-contract-stats', selectedDepartment?.id],
    queryFn: () =>
      creditPortfolioApi.getContractStats({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Filter contracts by search text and paginate
  const filteredContracts = useMemo(() => {
    if (!contracts) return []

    let filtered = contracts

    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase()
      filtered = contracts.filter((contract: FinContract) =>
        contract.contract_number.toLowerCase().includes(searchLower) ||
        contract.counterparty?.toLowerCase().includes(searchLower) ||
        contract.contract_type?.toLowerCase().includes(searchLower)
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
      // Sum total_paid if available, otherwise sum principal and interest
      const total =
        contract.total_paid ||
        (contract.principal || 0) + (contract.interest || 0)
      return sum + total
    }, 0)
  }, [paginatedContracts])

  const columns = [
    {
      title: 'Номер договора',
      dataIndex: 'contract_number',
      key: 'contract_number',
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Дата договора',
      dataIndex: 'contract_date',
      key: 'contract_date',
      render: (date: string | null) =>
        date ? dayjs(date).format('DD.MM.YYYY') : '—',
      sorter: (a: FinContract, b: FinContract) => {
        if (!a.contract_date) return 1
        if (!b.contract_date) return -1
        return new Date(a.contract_date).getTime() - new Date(b.contract_date).getTime()
      },
    },
    {
      title: 'Тип договора',
      dataIndex: 'contract_type',
      key: 'contract_type',
      render: (type: string | null) =>
        type ? (
          <Tag color={type === 'Кредит' ? 'blue' : 'green'}>{type}</Tag>
        ) : (
          '—'
        ),
    },
    {
      title: 'Контрагент',
      dataIndex: 'counterparty',
      key: 'counterparty',
      ellipsis: true,
      render: (text: string | null) => text || '—',
    },
    {
      title: 'Всего выплачено',
      dataIndex: 'total_paid',
      key: 'total_paid',
      align: 'right' as const,
      render: (value: number | null) =>
        value ? `${value.toLocaleString('ru-RU')} ₽` : '—',
      sorter: (a: FinContract, b: FinContract) =>
        (a.total_paid || 0) - (b.total_paid || 0),
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>
          {isActive ? 'Активен' : 'Закрыт'}
        </Tag>
      ),
    },
  ]

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
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Кредитный портфель - Договоры</h1>
        <p style={{ margin: '8px 0 0 0', color: '#8c8c8c' }}>
          Детальная информация по кредитным договорам
        </p>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Всего договоров"
              value={filteredContracts.length}
              suffix={`/ ${contractStats?.total_count || 0}`}
              prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Сумма на странице"
              value={currentPageTotal}
              precision={0}
              suffix="₽"
              prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 8 }}>
              {paginatedContracts.length} договоров из {filteredContracts.length}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Активные"
              value={contractStats?.active_count || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Закрытые"
              value={contractStats?.closed_count || 0}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap style={{ width: '100%' }}>
          <Search
            placeholder="Поиск по номеру, контрагенту..."
            allowClear
            style={{ width: 300 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Статус"
            allowClear
            style={{ width: 150 }}
            value={filterActive}
            onChange={setFilterActive}
          >
            <Select.Option value={true}>Активные</Select.Option>
            <Select.Option value={false}>Закрытые</Select.Option>
          </Select>
          <Select
            placeholder="Тип договора"
            allowClear
            style={{ width: 150 }}
            value={filterType}
            onChange={setFilterType}
          >
            <Select.Option value="Кредит">Кредит</Select.Option>
            <Select.Option value="Заем">Заем</Select.Option>
          </Select>
          <Button
            icon={<FilterOutlined />}
            onClick={() => {
              setSearchText('')
              setFilterActive(undefined)
              setFilterType(undefined)
            }}
          >
            Сбросить
          </Button>
        </Space>
      </Card>

      {/* Contracts Table */}
      <Card>
        {filteredContracts.length === 0 ? (
          <Empty
            description={
              debouncedSearch || debouncedFilterActive !== undefined || debouncedFilterType
                ? 'Договоры не найдены по заданным фильтрам'
                : 'Договоры не найдены'
            }
          />
        ) : (
          <>
            <Table
              columns={columns}
              dataSource={paginatedContracts}
              rowKey="id"
              pagination={false}
              loading={isLoading}
            />

            {/* Pagination */}
            {filteredContracts.length > PAGE_SIZE && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginTop: 24,
                paddingTop: 16,
                borderTop: '1px solid #f0f0f0'
              }}>
                <Pagination
                  current={currentPage}
                  pageSize={PAGE_SIZE}
                  total={filteredContracts.length}
                  onChange={setCurrentPage}
                  showSizeChanger={false}
                  showTotal={(total, range) =>
                    `Страница ${currentPage} из ${Math.ceil(total / PAGE_SIZE)} (${range[0]}-${range[1]} из ${total} договоров)`
                  }
                />
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
