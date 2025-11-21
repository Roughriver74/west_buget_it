/**
 * Module Settings Page - Admin only
 *
 * Allows ADMIN users to:
 * - View all available modules
 * - Enable/disable modules for organizations
 * - View module dependencies and details
 */

import React, { useState } from 'react'
import {
  Typography,
  Card,
  Space,
  Select,
  Table,
  Switch,
  Tag,
  Tooltip,
  message,
  Alert,
  Spin,
  Button,
} from 'antd'
import {
  InfoCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Module, EnabledModulesResponse } from '@/types/module'
import * as modulesApi from '@/api/modules'
import * as organizationsApi from '@/api/organizations'
import type { ColumnsType } from 'antd/es/table'

const { Title, Paragraph, Text } = Typography

const ModuleSettingsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [selectedOrgId, setSelectedOrgId] = useState<number | undefined>()

  // Fetch organizations
  const { data: organizations, isLoading: orgsLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.getOrganizations(),
  })

  // Fetch all modules
  const { data: allModules, isLoading: modulesLoading } = useQuery<Module[]>({
    queryKey: ['modules', 'all'],
    queryFn: () => modulesApi.getModules({ active_only: true }),
  })

  // Fetch enabled modules for selected organization
  const { data: enabledModules, isLoading: enabledLoading } = useQuery<EnabledModulesResponse>({
    queryKey: ['modules', 'enabled', selectedOrgId],
    queryFn: () => modulesApi.getOrganizationEnabledModules(selectedOrgId!, { include_expired: false }),
    enabled: !!selectedOrgId,
  })

  // Enable module mutation
  const enableModuleMutation = useMutation({
    mutationFn: (moduleCode: string) =>
      modulesApi.enableModule({
        module_code: moduleCode,
        organization_id: selectedOrgId!,
      }),
    onSuccess: (_, moduleCode) => {
      message.success(`Модуль успешно включен`)
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled', selectedOrgId] })
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled', 'my'] }) // Refresh context
    },
    onError: (error: any) => {
      message.error(`Ошибка при включении модуля: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Disable module mutation
  const disableModuleMutation = useMutation({
    mutationFn: (moduleCode: string) =>
      modulesApi.disableModule({
        module_code: moduleCode,
        organization_id: selectedOrgId!,
      }),
    onSuccess: (_, moduleCode) => {
      message.success(`Модуль успешно отключен`)
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled', selectedOrgId] })
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled', 'my'] }) // Refresh context
    },
    onError: (error: any) => {
      message.error(`Ошибка при отключении модуля: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleToggleModule = (moduleCode: string, enabled: boolean) => {
    if (!selectedOrgId) {
      message.warning('Выберите организацию')
      return
    }

    if (moduleCode === 'BUDGET_CORE' && !enabled) {
      message.warning('Базовый модуль нельзя отключить')
      return
    }

    if (enabled) {
      enableModuleMutation.mutate(moduleCode)
    } else {
      disableModuleMutation.mutate(moduleCode)
    }
  }

  const isModuleEnabled = (moduleCode: string): boolean => {
    if (!enabledModules) return false
    return enabledModules.modules.some((m) => m.code === moduleCode)
  }

  // Table columns
  const columns: ColumnsType<Module> = [
    {
      title: 'Модуль',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>{record.icon || '📦'}</Text>
            <Text strong>{text}</Text>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.code}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text type="secondary">{text || 'Нет описания'}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Версия',
      dataIndex: 'version',
      key: 'version',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: 'Зависимости',
      dataIndex: 'dependencies',
      key: 'dependencies',
      width: 200,
      render: (deps: string[] | undefined) => {
        if (!deps || deps.length === 0) {
          return <Text type="secondary">Нет</Text>
        }
        return (
          <Space size={4} wrap>
            {deps.map((dep) => (
              <Tag key={dep} color="blue" style={{ fontSize: 11 }}>
                {dep}
              </Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: 'Статус',
      key: 'status',
      width: 120,
      align: 'center',
      render: (_, record) => {
        const enabled = isModuleEnabled(record.code)
        return (
          <Space>
            <Switch
              checked={enabled}
              loading={enableModuleMutation.isPending || disableModuleMutation.isPending}
              disabled={!selectedOrgId || record.code === 'BUDGET_CORE'}
              onChange={(checked) => handleToggleModule(record.code, checked)}
              checkedChildren={<CheckCircleOutlined />}
              unCheckedChildren={<CloseCircleOutlined />}
            />
            {enabled ? (
              <Tag color="success">Включен</Tag>
            ) : (
              <Tag color="default">Выключен</Tag>
            )}
          </Space>
        )
      },
    },
  ]

  const isLoading = modulesLoading || orgsLoading || (selectedOrgId && enabledLoading)

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Title level={3} style={{ margin: 0 }}>
              ⚙️ Управление модулями
            </Title>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              Включите или отключите функциональные модули для организаций.
              Модуль BUDGET_CORE является обязательным и не может быть отключен.
            </Paragraph>
          </Space>
        </Card>

        {/* Alert: Module system temporary disabled */}
        <Alert
          message="Система модулей временно отключена"
          description="В данный момент все модули доступны всем пользователям для обеспечения обратной совместимости. Настройки на этой странице будут применены после активации системы модулей."
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />

        {/* Organization Selector */}
        <Card>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Text strong>Выберите организацию</Text>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                (обязательно для настройки модулей)
              </Text>
            </div>
            <Select
              style={{ width: '100%', maxWidth: 500 }}
              placeholder="Выберите организацию"
              value={selectedOrgId}
              onChange={setSelectedOrgId}
              loading={orgsLoading}
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={organizations?.map((org) => ({
                value: org.id,
                label: `${org.name} ${org.inn ? `(ИНН: ${org.inn})` : ''}`,
              }))}
            />
            {selectedOrgId && enabledModules && (
              <Alert
                message={`Организация: ${enabledModules.organization_name}`}
                description={`Включено модулей: ${enabledModules.modules.length} из ${allModules?.length || 0}`}
                type="success"
                showIcon
              />
            )}
          </Space>
        </Card>

        {/* Modules Table */}
        <Card
          title={
            <Space>
              <Text strong>Доступные модули</Text>
              <Text type="secondary">({allModules?.length || 0})</Text>
            </Space>
          }
          extra={
            selectedOrgId && (
              <Button
                icon={<ReloadOutlined />}
                onClick={() => queryClient.invalidateQueries({ queryKey: ['modules'] })}
              >
                Обновить
              </Button>
            )
          }
        >
          <Spin spinning={isLoading}>
            <Table
              columns={columns}
              dataSource={allModules}
              rowKey="id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `Всего модулей: ${total}`,
              }}
              size="middle"
              locale={{
                emptyText: 'Нет доступных модулей',
              }}
            />
          </Spin>
        </Card>

        {/* Info Card */}
        <Card>
          <Space direction="vertical" size="small">
            <Text strong>📚 Описание модулей</Text>
            <ul style={{ marginLeft: 20, marginTop: 8 }}>
              <li>
                <Text strong>BUDGET_CORE</Text> - Базовый модуль с основным функционалом (обязателен)
              </li>
              <li>
                <Text strong>PAYROLL_KPI</Text> - Фонд оплаты труда и система KPI
              </li>
              <li>
                <Text strong>AI_FORECAST</Text> - AI-классификация транзакций и прогнозирование
              </li>
              <li>
                <Text strong>CREDIT_PORTFOLIO</Text> - Управление кредитным портфелем
              </li>
              <li>
                <Text strong>REVENUE_BUDGET</Text> - Планирование доходов и метрики клиентов
              </li>
              <li>
                <Text strong>INTEGRATIONS_1C</Text> - Интеграция с 1С через OData
              </li>
              <li>
                <Text strong>FOUNDER_DASHBOARD</Text> - Executive dashboard для руководителя
              </li>
              <li>
                <Text strong>ADVANCED_ANALYTICS</Text> - Расширенная аналитика и отчеты
              </li>
              <li>
                <Text strong>MULTI_DEPARTMENT</Text> - Управление несколькими отделами
              </li>
              <li>
                <Text strong>HR_DEPARTMENT</Text> - Табель учета рабочего времени
              </li>
              <li>
                <Text strong>INVOICE_PROCESSING</Text> - AI обработка счетов (OCR)
              </li>
            </ul>
          </Space>
        </Card>
      </Space>
    </div>
  )
}

export default ModuleSettingsPage
