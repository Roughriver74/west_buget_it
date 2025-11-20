import { Card, Typography, Steps, Tag, Space, Divider, Alert } from 'antd'
import {
  EditOutlined,
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  UserOutlined,
  SafetyOutlined,
  DollarOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface KpiWorkflowDiagramProps {
  compact?: boolean
}

export const KpiWorkflowDiagram = ({ compact = false }: KpiWorkflowDiagramProps) => {
  const workflowSteps = [
    {
      title: 'DRAFT',
      description: 'Черновик',
      icon: <EditOutlined />,
      status: 'process' as const,
      color: '#faad14',
      details: [
        'Создание новой записи KPI',
        'Назначение целей с весами',
        'Настройка бонусов',
        'sum(weights) = 100%',
      ],
      actions: ['Редактирование', 'Отправка на проверку'],
      roles: ['USER', 'MANAGER', 'ADMIN'],
    },
    {
      title: 'UNDER_REVIEW',
      description: 'На проверке',
      icon: <SendOutlined />,
      status: 'process' as const,
      color: '#13c2c2',
      details: [
        'Заявка отправлена на проверку',
        'Ожидание решения менеджера',
        'Возможен возврат в DRAFT',
        'Возможно отклонение',
      ],
      actions: ['Утверждение', 'Отклонение', 'Возврат в черновик'],
      roles: ['MANAGER', 'ADMIN'],
    },
    {
      title: 'APPROVED',
      description: 'Утверждено',
      icon: <CheckCircleOutlined />,
      status: 'finish' as const,
      color: '#52c41a',
      details: [
        'KPI утверждён менеджером',
        'Автосинхронизация с PayrollPlan',
        'Автопересчёт бонусов',
        'Бонусы включены в зарплату',
      ],
      actions: ['Синхронизация с PayrollPlan', 'Расчёт бонусов'],
      roles: ['MANAGER', 'ADMIN'],
    },
    {
      title: 'REJECTED',
      description: 'Отклонено',
      icon: <CloseCircleOutlined />,
      status: 'error' as const,
      color: '#f5222d',
      details: [
        'KPI отклонён',
        'Указана причина отклонения',
        'Можно вернуть в DRAFT для исправления',
      ],
      actions: ['Возврат в черновик', 'Архивация'],
      roles: ['MANAGER', 'ADMIN'],
    },
  ]

  if (compact) {
    return (
      <div style={{ padding: '16px 0' }}>
        <Steps current={-1} size="small">
          {workflowSteps.map((step) => (
            <Step
              key={step.title}
              title={step.description}
              icon={step.icon}
              status={step.status}
            />
          ))}
        </Steps>
      </div>
    )
  }

  return (
    <Card title={<Space><FileTextOutlined /> Workflow: Процесс работы с KPI</Space>}>
      <Alert
        message="Жизненный цикл записи KPI"
        description="Каждая запись EmployeeKPI проходит через следующие статусы. Переходы между статусами контролируются системой ролей."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* Main Workflow Steps */}
      <Steps
        direction="vertical"
        current={-1}
        style={{ marginBottom: 32 }}
      >
        {workflowSteps.map((step) => (
          <Step
            key={step.title}
            title={
              <Space>
                <Tag color={step.color}>{step.title}</Tag>
                <Text strong>{step.description}</Text>
              </Space>
            }
            description={
              <div style={{ paddingTop: 8 }}>
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary">Описание:</Text>
                  <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                    {step.details.map((detail, i) => (
                      <li key={i}>
                        <Text>{detail}</Text>
                      </li>
                    ))}
                  </ul>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary">Доступные действия:</Text>
                  <div style={{ marginTop: 4 }}>
                    <Space wrap>
                      {step.actions.map((action) => (
                        <Tag key={action}>{action}</Tag>
                      ))}
                    </Space>
                  </div>
                </div>

                <div>
                  <Text type="secondary">Роли:</Text>
                  <div style={{ marginTop: 4 }}>
                    <Space wrap>
                      {step.roles.map((role) => (
                        <Tag key={role} icon={<UserOutlined />} color="blue">
                          {role}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </div>
              </div>
            }
            icon={step.icon}
            status={step.status}
          />
        ))}
      </Steps>

      <Divider />

      {/* Transitions */}
      <Title level={5}>Возможные переходы</Title>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Card size="small" type="inner">
            <Text strong>DRAFT → UNDER_REVIEW</Text>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              <Text type="secondary">
                • Отправка на проверку менеджеру
                <br />• Валидация: sum(weights) = 100%
                <br />• Доступно: USER, MANAGER, ADMIN
              </Text>
            </Paragraph>
          </Card>

          <Card size="small" type="inner">
            <Text strong>UNDER_REVIEW → APPROVED</Text>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              <Text type="secondary">
                • Утверждение менеджером/админом
                <br />
                • Автоматическая синхронизация с PayrollPlan
                <br />• Доступно: MANAGER, ADMIN
              </Text>
            </Paragraph>
          </Card>

          <Card size="small" type="inner">
            <Text strong>UNDER_REVIEW → REJECTED</Text>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              <Text type="secondary">
                • Отклонение с указанием причины
                <br />• Доступно: MANAGER, ADMIN
              </Text>
            </Paragraph>
          </Card>

          <Card size="small" type="inner">
            <Text strong>UNDER_REVIEW / REJECTED → DRAFT</Text>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              <Text type="secondary">
                • Возврат на доработку
                <br />• Доступно: MANAGER, ADMIN (из UNDER_REVIEW), любой (из REJECTED)
              </Text>
            </Paragraph>
          </Card>
        </Space>
      </div>

      <Divider />

      {/* Automatic Actions */}
      <Title level={5}>
        <Space>
          <SafetyOutlined />
          Автоматические действия системы
        </Space>
      </Title>
      <div style={{ marginBottom: 24 }}>
        <Card size="small" style={{ background: '#f0f5ff', borderColor: '#adc6ff' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <DollarOutlined style={{ color: '#1890ff', marginRight: 8 }} />
              <Text strong>При утверждении (APPROVED):</Text>
            </div>
            <ul style={{ marginLeft: 20, marginBottom: 0 }}>
              <li>
                <Text>
                  Автоматическая синхронизация с <Text code>PayrollPlan</Text>
                </Text>
              </li>
              <li>
                <Text>
                  Создание/обновление записи плана зарплаты с бонусами
                </Text>
              </li>
              <li>
                <Text>
                  Расчёт бонусов: месячный, квартальный, годовой
                </Text>
              </li>
              <li>
                <Text>
                  Логирование операции в <Text code>notes</Text>
                </Text>
              </li>
            </ul>
          </Space>
        </Card>
      </div>

      <Divider />

      {/* Best Practices */}
      <Title level={5}>💡 Рекомендации</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="Порядок работы"
          description={
            <ol style={{ paddingLeft: 20, marginBottom: 0 }}>
              <li>Создайте черновик (DRAFT) и назначьте цели с весами</li>
              <li>Убедитесь, что сумма весов = 100%</li>
              <li>Настройте бонусы и множители</li>
              <li>Отправьте на проверку менеджеру</li>
              <li>Менеджер утверждает → автосинхронизация с зарплатой</li>
            </ol>
          }
          type="success"
          showIcon
        />

        <Alert
          message="Валидация"
          description="Система автоматически проверяет, что сумма весов целей равна 100%. Без этого отправка на проверку невозможна."
          type="warning"
          showIcon
        />
      </Space>
    </Card>
  )
}
