/**
 * Module Settings Page - Управление модулями для организации
 * ADMIN only
 */

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Spin,
  Typography,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Switch,
  Modal,
  Form,
  Input,
  DatePicker,
} from 'antd'
import {
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import * as modulesApi from '@/api/modules'
import { organizationsApi } from '@/api/organizations'
import type {
  Module,
  ModuleStatistics,
  EnabledModuleInfo,
  ModuleEnableRequest,
} from '@/types/module'
import type { Organization } from '@/types'
import dayjs from 'dayjs'

const { Title, Text } = Typography

interface ModuleWithStatus extends Module {
  isEnabled: boolean
  expiresAt?: string
  enabledOrgs?: number
}

const ModuleSettingsPage = () => {
  const queryClient = useQueryClient()
  const [selectedOrganization, setSelectedOrganization] = useState<number>(1) // Default org
  const [enableModalVisible, setEnableModalVisible] = useState(false)
  const [selectedModule, setSelectedModule] = useState<Module | null>(null)
  const [form] = Form.useForm()

  // Fetch all modules
  const {
    data: allModules = [],
    isLoading: modulesLoading,
    refetch: refetchModules,
  } = useQuery<Module[]>({
    queryKey: ['modules', { active_only: false }],
    queryFn: () => modulesApi.getModules({ active_only: false }),
  })

  // Fetch enabled modules for selected organization
  const {
    data: enabledModulesData,
    isLoading: enabledLoading,
    refetch: refetchEnabled,
  } = useQuery({
    queryKey: ['organization-enabled-modules', selectedOrganization],
    queryFn: () => modulesApi.getOrganizationEnabledModules(selectedOrganization),
    enabled: !!selectedOrganization,
  })

  // Fetch statistics
  const { data: statistics = [] } = useQuery<ModuleStatistics[]>({
    queryKey: ['module-statistics'],
    queryFn: modulesApi.getModuleStatistics,
  })

  // Fetch organizations
  const { data: organizations = [] } = useQuery<Organization[]>({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.getAll({ is_active: true }),
  })

  // Enable module mutation
  const enableMutation = useMutation({
    mutationFn: (data: ModuleEnableRequest) => modulesApi.enableModule(data),
    onSuccess: () => {
      message.success('Модуль успешно включен')
      refetchEnabled()
      queryClient.invalidateQueries({ queryKey: ['module-statistics'] })
      setEnableModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.message || 'Ошибка при включении модуля')
    },
  })

  // Disable module mutation
  const disableMutation = useMutation({
    mutationFn: (data: { module_code: string; organization_id: number }) =>
      modulesApi.disableModule(data),
    onSuccess: () => {
      message.success('Модуль успешно отключен')
      refetchEnabled()
      queryClient.invalidateQueries({ queryKey: ['module-statistics'] })
    },
    onError: (error: any) => {
      message.error(error.message || 'Ошибка при отключении модуля')
    },
  })

  // Combine modules with enabled status
  const modulesWithStatus = useMemo<ModuleWithStatus[]>(() => {
    if (!allModules || !Array.isArray(allModules)) {
      return []
    }

    const enabledModules = enabledModulesData?.modules || []
    const statsMap = new Map(statistics.map((s) => [s.module_code, s]))

    return allModules.map((module) => {
      const enabled = enabledModules.find((e) => e.code === module.code)
      const stats = statsMap.get(module.code)

      return {
        ...module,
        isEnabled: !!enabled && !enabled.is_expired,
        expiresAt: enabled?.expires_at,
        enabledOrgs: stats?.active_organizations || 0,
      }
    })
  }, [allModules, enabledModulesData, statistics])

  // Handle enable module
  const handleEnableModule = (module: Module) => {
    setSelectedModule(module)
    setEnableModalVisible(true)
  }

  // Handle disable module
  const handleDisableModule = (module: Module) => {
    disableMutation.mutate({
      module_code: module.code,
      organization_id: selectedOrganization,
    })
  }

  // Handle enable form submit
  const handleEnableSubmit = () => {
    form.validateFields().then((values) => {
      enableMutation.mutate({
        module_code: selectedModule!.code,
        organization_id: selectedOrganization,
        expires_at: values.expires_at ? values.expires_at.toISOString() : undefined,
        limits: values.limits ? JSON.parse(values.limits) : {},
      })
    })
  }

  // Table columns
  const columns: ColumnsType<ModuleWithStatus> = [
    {
      title: 'Код',
      dataIndex: 'code',
      key: 'code',
      width: 200,
      render: (code: string) => <Text strong>{code}</Text>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Версия',
      dataIndex: 'version',
      key: 'version',
      width: 100,
      align: 'center',
      render: (version?: string) => <Tag color="blue">{version || 'N/A'}</Tag>,
    },
    {
      title: 'Активен',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center',
      render: (isActive: boolean) =>
        isActive ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            Да
          </Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="default">
            Нет
          </Tag>
        ),
    },
    {
      title: 'Включен для организации',
      dataIndex: 'isEnabled',
      key: 'isEnabled',
      width: 180,
      align: 'center',
      render: (isEnabled: boolean, record) =>
        isEnabled ? (
          <Space direction="vertical" size={0}>
            <Tag icon={<CheckCircleOutlined />} color="success">
              Включен
            </Tag>
            {record.expiresAt && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                До: {dayjs(record.expiresAt).format('DD.MM.YYYY')}
              </Text>
            )}
          </Space>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="default">
            Отключен
          </Tag>
        ),
    },
    {
      title: 'Всего организаций',
      dataIndex: 'enabledOrgs',
      key: 'enabledOrgs',
      width: 150,
      align: 'center',
      render: (count: number) => <Text>{count}</Text>,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      align: 'center',
      fixed: 'right',
      render: (_: any, record: ModuleWithStatus) => (
        <Space size="small">
          {record.isEnabled ? (
            <Popconfirm
              title="Отключить модуль?"
              description={`Вы уверены, что хотите отключить модуль "${record.name}"?`}
              onConfirm={() => handleDisableModule(record)}
              okText="Да"
              cancelText="Отмена"
            >
              <Button danger size="small" loading={disableMutation.isPending}>
                Отключить
              </Button>
            </Popconfirm>
          ) : (
            <Button
              type="primary"
              size="small"
              onClick={() => handleEnableModule(record)}
              loading={enableMutation.isPending}
              disabled={!record.is_active}
            >
              Включить
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const isLoading = modulesLoading || enabledLoading

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined /> Управление модулями
        </Title>
        <Text type="secondary">
          Управление доступом к модулям для организаций (только для администратора)
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего модулей"
              value={allModules.length}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Активных модулей"
              value={allModules.filter((m) => m.is_active).length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Включено для организации"
              value={modulesWithStatus.filter((m) => m.isEnabled).length}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего организаций"
              value={organizations.length}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Table */}
      <Card
        title={
          <Space>
            <Text strong>Список модулей</Text>
            <Text type="secondary">
              (Организация: {enabledModulesData?.organization_name || 'Загрузка...'})
            </Text>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => refetchModules()}>
              Обновить
            </Button>
          </Space>
        }
      >
        <Spin spinning={isLoading} tip="Загрузка модулей...">
          <Table
            columns={columns}
            dataSource={modulesWithStatus}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `Всего: ${total}`,
            }}
            scroll={{ x: 1400 }}
          />
        </Spin>
      </Card>

      {/* Enable Module Modal */}
      <Modal
        title={`Включить модуль: ${selectedModule?.name}`}
        open={enableModalVisible}
        onOk={handleEnableSubmit}
        onCancel={() => {
          setEnableModalVisible(false)
          form.resetFields()
        }}
        confirmLoading={enableMutation.isPending}
        okText="Включить"
        cancelText="Отмена"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label="Организация"
            help="Модуль будет включен для выбранной организации"
          >
            <Text strong>{enabledModulesData?.organization_name}</Text>
          </Form.Item>

          <Form.Item
            label="Код модуля"
            help="Уникальный идентификатор модуля"
          >
            <Text code>{selectedModule?.code}</Text>
          </Form.Item>

          <Form.Item
            label="Дата окончания"
            name="expires_at"
            help="Оставьте пустым для бессрочного доступа"
          >
            <DatePicker
              style={{ width: '100%' }}
              format="DD.MM.YYYY"
              placeholder="Выберите дату"
            />
          </Form.Item>

          <Form.Item
            label="Лимиты (JSON)"
            name="limits"
            help='Пример: {"max_users": 100}'
          >
            <Input.TextArea
              rows={4}
              placeholder='{"max_users": 100, "max_contracts": 50}'
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ModuleSettingsPage
