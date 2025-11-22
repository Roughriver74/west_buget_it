import { useState } from 'react'
import {
  Table,
  Card,
  Button,
  Tag,
  Space,
  Typography,
  Switch,
  Tooltip,
  message,
  Descriptions
} from 'antd'
import {
  AppstoreAddOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as modulesApi from '@/api/modules'
import { Module, EnabledModuleInfo, ModuleCode } from '@/types/module'
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Title, Text, Paragraph } = Typography

const ModuleSettingsPage = () => {
  const { user } = useAuth()
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const isAdmin = user?.role === 'ADMIN'

  // Fetch all available modules (metadata)
  const {
    data: availableModules,
    isLoading: isLoadingAvailable
  } = useQuery({
    queryKey: ['modules', 'all'],
    queryFn: () => modulesApi.getModules(),
    staleTime: 5 * 60 * 1000
  })

  // Fetch enabled modules for current organization
  const {
    data: enabledModulesData,
    isLoading: isLoadingEnabled,
    refetch: refetchEnabled
  } = useQuery({
    queryKey: ['modules', 'enabled', 'my'],
    queryFn: () => modulesApi.getMyEnabledModules({ include_expired: true })
  })

  // Mutations
  const enableMutation = useMutation({
    mutationFn: modulesApi.enableModule,
    onSuccess: () => {
      message.success('Модуль успешно включен')
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled'] })
    },
    onError: () => message.error('Не удалось включить модуль')
  })

  const disableMutation = useMutation({
    mutationFn: modulesApi.disableModule,
    onSuccess: () => {
      message.success('Модуль успешно отключен')
      queryClient.invalidateQueries({ queryKey: ['modules', 'enabled'] })
    },
    onError: () => message.error('Не удалось отключить модуль')
  })

  const handleToggleModule = (moduleCode: string, enabled: boolean) => {
    if (!enabledModulesData?.organization_id) return

    if (enabled) {
      enableMutation.mutate({
        module_code: moduleCode,
        organization_id: enabledModulesData.organization_id,
        // default to 1 year
        expires_at: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString()
      })
    } else {
      disableMutation.mutate({
        module_code: moduleCode,
        organization_id: enabledModulesData.organization_id
      })
    }
  }

  const loading = isLoadingAvailable || isLoadingEnabled

  // Merge data
  const tableData = availableModules?.map(mod => {
    const enabledInfo = enabledModulesData?.modules?.find(m => m.code === mod.code)
    return {
      ...mod,
      enabled: !!enabledInfo && !enabledInfo.is_expired,
      enabledAt: enabledInfo?.enabled_at,
      expiresAt: enabledInfo?.expires_at,
      isExpired: enabledInfo?.is_expired
    }
  }) || []

  const columns = [
    {
      title: 'Модуль',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.code}</Text>
        </Space>
      )
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Статус',
      key: 'status',
      render: (_: any, record: any) => (
        <Space>
          {record.enabled ? (
            <Tag color="success" icon={<CheckCircleOutlined />}>
              Активен
            </Tag>
          ) : record.isExpired ? (
            <Tag color="warning" icon={<CloseCircleOutlined />}>
              Истек
            </Tag>
          ) : (
            <Tag color="default">
              Отключен
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: any) => (
        <Switch
          checked={record.enabled}
          onChange={(checked) => handleToggleModule(record.code, checked)}
          loading={enableMutation.isPending || disableMutation.isPending}
          disabled={!isAdmin}
        />
      )
    }
  ]

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <AppstoreAddOutlined /> Управление модулями
          </Title>
          <Paragraph type="secondary">
            Включение и отключение функциональных модулей системы для организации
          </Paragraph>
        </div>

        {enabledModulesData?.organization_name && (
           <Card size="small">
             <Descriptions>
               <Descriptions.Item label="Организация">
                 {enabledModulesData.organization_name}
               </Descriptions.Item>
               <Descriptions.Item label="Активных модулей">
                 {enabledModulesData.modules?.filter(m => !m.is_expired).length || 0}
               </Descriptions.Item>
             </Descriptions>
           </Card>
        )}

        <Card
          extra={
            <Button icon={<ReloadOutlined />} onClick={() => refetchEnabled()}>
              Обновить
            </Button>
          }
        >
          <Table
            dataSource={tableData}
            columns={columns}
            rowKey="code"
            loading={loading}
            pagination={false}
          />
        </Card>
      </Space>
    </div>
  )
}

export default ModuleSettingsPage
