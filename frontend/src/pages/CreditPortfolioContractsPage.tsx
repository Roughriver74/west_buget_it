import { useState } from 'react'
import { Card, Table, Tag, Button, Space, Input, Select, Empty, Spin } from 'antd'
import { SearchOutlined, FilterOutlined, FileTextOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import type { FinContract } from '@/api/creditPortfolio'
import dayjs from 'dayjs'

const { Search } = Input

export default function CreditPortfolioContractsPage() {
  const { selectedDepartment } = useDepartment()
  const [searchText, setSearchText] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)
  const [filterType, setFilterType] = useState<string | undefined>(undefined)

  const { data: contracts, isLoading } = useQuery({
    queryKey: ['credit-contracts', selectedDepartment?.id, filterActive],
    queryFn: () =>
      creditPortfolioApi.getContracts({
        department_id: selectedDepartment?.id,
        is_active: filterActive,
        contract_type: filterType,
      }),
    enabled: !!selectedDepartment,
  })

  const { data: contractStats } = useQuery({
    queryKey: ['credit-contract-stats', selectedDepartment?.id],
    queryFn: () =>
      creditPortfolioApi.getContractStats({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Filter contracts by search text
  const filteredContracts = contracts?.filter((contract: FinContract) => {
    if (!searchText) return true
    const searchLower = searchText.toLowerCase()
    return (
      contract.contract_number.toLowerCase().includes(searchLower) ||
      contract.counterparty?.toLowerCase().includes(searchLower) ||
      contract.contract_type?.toLowerCase().includes(searchLower)
    )
  })

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
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>
          {isActive ? 'Активен' : 'Закрыт'}
        </Tag>
      ),
      filters: [
        { text: 'Активные', value: true },
        { text: 'Закрытые', value: false },
      ],
      onFilter: (value: any, record: FinContract) =>
        record.is_active === value,
    },
  ]

  if (isLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>Кредитный портфель - Договоры</h1>

      {/* Statistics Cards */}
      {contractStats && (
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginBottom: 24,
            flexWrap: 'wrap',
          }}
        >
          <Card style={{ flex: 1, minWidth: 200 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 14, color: '#8c8c8c' }}>Всего договоров</div>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {contractStats.total_count || 0}
              </div>
            </div>
          </Card>
          <Card style={{ flex: 1, minWidth: 200 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 14, color: '#8c8c8c' }}>Активные</div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                {contractStats.active_count || 0}
              </div>
            </div>
          </Card>
          <Card style={{ flex: 1, minWidth: 200 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 14, color: '#8c8c8c' }}>Закрытые</div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#8c8c8c' }}>
                {contractStats.closed_count || 0}
              </div>
            </div>
          </Card>
        </div>
      )}

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
        {!filteredContracts || filteredContracts.length === 0 ? (
          <Empty description="Договоры не найдены" />
        ) : (
          <Table
            columns={columns}
            dataSource={filteredContracts}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `Всего: ${total} договоров`,
            }}
          />
        )}
      </Card>
    </div>
  )
}
