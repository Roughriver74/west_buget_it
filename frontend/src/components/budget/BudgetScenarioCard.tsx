/**
 * Budget Scenario Card Component
 * Displays a budget scenario with key parameters
 */
import React from 'react'
import { Card, Tag, Descriptions, Typography, Space, Button, Popconfirm } from 'antd'
import { EditOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { BudgetScenarioType } from '@/types/budgetPlanning'
import type { BudgetScenario } from '@/types/budgetPlanning'

const { Text, Title } = Typography

interface BudgetScenarioCardProps {
  scenario: BudgetScenario
  onEdit?: (scenario: BudgetScenario) => void
  onDelete?: (id: number) => void
  onSelect?: (scenario: BudgetScenario) => void
  selected?: boolean
}

const scenarioTypeColors: Record<BudgetScenarioType, string> = {
  [BudgetScenarioType.BASE]: 'blue',
  [BudgetScenarioType.OPTIMISTIC]: 'green',
  [BudgetScenarioType.PESSIMISTIC]: 'orange',
}

const scenarioTypeLabels: Record<BudgetScenarioType, string> = {
  [BudgetScenarioType.BASE]: 'Базовый',
  [BudgetScenarioType.OPTIMISTIC]: 'Оптимистичный',
  [BudgetScenarioType.PESSIMISTIC]: 'Пессимистичный',
}

export const BudgetScenarioCard: React.FC<BudgetScenarioCardProps> = ({
  scenario,
  onEdit,
  onDelete,
  onSelect,
  selected = false,
}) => {
  const { scenario_name, scenario_type, year, global_growth_rate, inflation_rate, fx_rate, description } = scenario

  return (
    <Card
      style={{
        marginBottom: 16,
        border: selected ? '2px solid #1890ff' : undefined,
        boxShadow: selected ? '0 4px 12px rgba(24, 144, 255, 0.2)' : undefined,
      }}
      actions={[
        onEdit && (
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => onEdit(scenario)}
            key="edit"
          >
            Редактировать
          </Button>
        ),
        onDelete && (
          <Popconfirm
            title="Удалить сценарий?"
            description="Это действие нельзя отменить"
            onConfirm={() => onDelete(scenario.id)}
            okText="Да"
            cancelText="Нет"
            key="delete"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Удалить
            </Button>
          </Popconfirm>
        ),
        onSelect && (
          <Button
            type={selected ? 'primary' : 'link'}
            icon={selected ? <CheckCircleOutlined /> : undefined}
            onClick={() => onSelect(scenario)}
            key="select"
          >
            {selected ? 'Выбран' : 'Выбрать'}
          </Button>
        ),
      ].filter(Boolean)}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>
            {scenario_name}
          </Title>
          <Space>
            <Tag color={scenarioTypeColors[scenario_type]}>
              {scenarioTypeLabels[scenario_type]}
            </Tag>
            <Tag>{year} год</Tag>
          </Space>
        </div>

        {description && (
          <Text type="secondary">{description}</Text>
        )}

        <Descriptions column={2} size="small">
          <Descriptions.Item label="Рост расходов">
            <Text strong>{global_growth_rate}%</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Инфляция">
            <Text strong>{inflation_rate}%</Text>
          </Descriptions.Item>
          {fx_rate && (
            <Descriptions.Item label="Курс валюты" span={2}>
              <Text strong>{fx_rate}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Space>
    </Card>
  )
}
