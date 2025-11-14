import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Button,
  Space,
  Breadcrumb,
  Descriptions,
  Tag,
  Select,
  Spin,
  Alert,
  Row,
  Col,
  Statistic,
} from 'antd'
import {
  LeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { RevenuePlanDetailsTable } from '@/components/revenue/RevenuePlanDetailsTable'
import { revenueApi } from '@/api/revenue'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs from 'dayjs'

const { Option } = Select

const RevenuePlanDetailsPage = () => {
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const { selectedDepartment } = useDepartment()
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null)

  // Fetch plan
  const { data: plan, isLoading: isPlanLoading } = useQuery({
    queryKey: ['revenue-plan', planId],
    queryFn: () => revenueApi.plans.getById(Number(planId)),
    enabled: !!planId,
  })

  // Fetch versions
  const { data: versions = [], isLoading: isVersionsLoading } = useQuery({
    queryKey: ['revenue-plan-versions', planId],
    queryFn: () => revenueApi.plans.getVersions(Number(planId)),
    enabled: !!planId,
  })

  // Fetch streams
  const { data: streams = [] } = useQuery({
    queryKey: ['revenue-streams', selectedDepartment?.id],
    queryFn: () =>
      revenueApi.streams.getAll({
        department_id: selectedDepartment?.id,
        is_active: true,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['revenue-categories', selectedDepartment?.id],
    queryFn: () =>
      revenueApi.categories.getAll({
        department_id: selectedDepartment?.id,
        is_active: true,
      }),
    enabled: !!selectedDepartment,
  })

  // Auto-select latest version
  useState(() => {
    if (versions.length > 0 && !selectedVersionId) {
      setSelectedVersionId(versions[0].id)
    }
  })

  const selectedVersion = versions.find((v) => v.id === selectedVersionId)
  const isEditable = selectedVersion?.status === 'DRAFT'

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: JSX.Element; text: string }> = {
      DRAFT: { color: 'default', icon: <ClockCircleOutlined />, text: 'Черновик' },
      IN_REVIEW: { color: 'processing', icon: <ClockCircleOutlined />, text: 'На согласовании' },
      APPROVED: { color: 'success', icon: <CheckCircleOutlined />, text: 'Утвержден' },
      REJECTED: { color: 'error', icon: <ClockCircleOutlined />, text: 'Отклонен' },
      ARCHIVED: { color: 'default', icon: <ClockCircleOutlined />, text: 'Архив' },
    }

    const config = statusConfig[status] || { color: 'default', icon: null, text: status }

    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  if (!selectedDepartment || isPlanLoading || isVersionsLoading) {
    return (
      <div style={{ padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <Spin size="large" tip="Загрузка данных плана...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  if (!plan) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="План не найден"
          description="Запрошенный план доходов не существует или у вас нет к нему доступа"
          type="error"
          showIcon
        />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <a onClick={() => navigate('/revenue/planning')}>Планирование доходов</a>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{plan.name}</Breadcrumb.Item>
      </Breadcrumb>

      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button
            icon={<LeftOutlined />}
            onClick={() => navigate('/revenue/planning')}
          >
            Назад
          </Button>
          <div>
            <h1 style={{ margin: 0 }}>{plan.name}</h1>
            <p style={{ margin: 0, color: '#8c8c8c' }}>
              Детальное планирование доходов по месяцам
            </p>
          </div>
        </div>
        {getStatusTag(plan.status)}
      </div>

      {/* Plan Info */}
      <Card style={{ marginBottom: 24 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="Год">{plan.year}</Descriptions.Item>
          <Descriptions.Item label="Создан">
            {dayjs(plan.created_at).format('DD.MM.YYYY HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="Общая плановая выручка">
            {new Intl.NumberFormat('ru-RU', {
              style: 'currency',
              currency: 'RUB',
              minimumFractionDigits: 0,
            }).format(plan.total_planned_revenue || 0)}
          </Descriptions.Item>
          {plan.description && (
            <Descriptions.Item label="Описание" span={4}>
              {plan.description}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Version Selector */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col span={12}>
            <Space>
              <span style={{ fontWeight: 500 }}>Версия плана:</span>
              <Select
                style={{ width: 300 }}
                value={selectedVersionId}
                onChange={setSelectedVersionId}
                placeholder="Выберите версию"
              >
                {versions.map((v) => (
                  <Option key={v.id} value={v.id}>
                    {v.version_name || `Версия ${v.version_number}`} -{' '}
                    {getStatusTag(v.status)}
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
          {selectedVersion && (
            <Col span={12} style={{ textAlign: 'right' }}>
              <Space size="large">
                <Statistic
                  title="Версия"
                  value={selectedVersion.version_number}
                  prefix="#"
                />
                <Statistic
                  title="Создана"
                  value={dayjs(selectedVersion.created_at).format('DD.MM.YYYY')}
                />
              </Space>
            </Col>
          )}
        </Row>
      </Card>

      {/* Details Table */}
      {selectedVersionId ? (
        <Card>
          <RevenuePlanDetailsTable
            versionId={selectedVersionId}
            streams={streams}
            categories={categories}
            isEditable={isEditable}
            onAfterSave={() => {
              // Refresh plan to update total
            }}
          />
        </Card>
      ) : (
        <Alert
          message="Выберите версию плана"
          description="Для начала работы выберите версию плана из списка выше"
          type="info"
          showIcon
        />
      )}
    </div>
  )
}

export default RevenuePlanDetailsPage
