/**
 * Budget Version Table Component
 * Displays budget versions with status and actions
 */
import React from 'react'
import { Table, Tag, Button, Space, Popconfirm, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SendOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { BudgetVersionStatus } from '@/types/budgetPlanning'
import type { BudgetVersion } from '@/types/budgetPlanning'
import dayjs from 'dayjs'

interface BudgetVersionTableProps {
  versions: BudgetVersion[]
  loading?: boolean
  onView?: (version: BudgetVersion) => void
  onEdit?: (version: BudgetVersion) => void
  onDelete?: (id: number) => void
  onSubmit?: (id: number) => void
  onCopy?: (version: BudgetVersion) => void
  selectedRowKeys?: number[]
  onSelectionChange?: (selectedRowKeys: number[]) => void
}

const statusColors: Record<BudgetVersionStatus, string> = {
  [BudgetVersionStatus.DRAFT]: 'default',
  [BudgetVersionStatus.IN_REVIEW]: 'processing',
  [BudgetVersionStatus.REVISION_REQUESTED]: 'warning',
  [BudgetVersionStatus.APPROVED]: 'success',
  [BudgetVersionStatus.REJECTED]: 'error',
  [BudgetVersionStatus.ARCHIVED]: 'default',
}

const statusLabels: Record<BudgetVersionStatus, string> = {
  [BudgetVersionStatus.DRAFT]: 'Черновик',
  [BudgetVersionStatus.IN_REVIEW]: 'На согласовании',
  [BudgetVersionStatus.REVISION_REQUESTED]: 'Требуется доработка',
  [BudgetVersionStatus.APPROVED]: 'Утверждена',
  [BudgetVersionStatus.REJECTED]: 'Отклонена',
  [BudgetVersionStatus.ARCHIVED]: 'Архив',
}

export const BudgetVersionTable: React.FC<BudgetVersionTableProps> = ({
  versions,
  loading = false,
  onView,
  onEdit,
  onDelete,
  onSubmit,
  onCopy,
  selectedRowKeys,
  onSelectionChange,
}) => {
  const columns: ColumnsType<BudgetVersion> = [
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 80,
      sorter: (a, b) => a.year - b.year,
    },
    {
      title: 'Версия',
      dataIndex: 'version_number',
      key: 'version_number',
      width: 80,
      render: (num) => `v${num}`,
    },
    {
      title: 'Название',
      dataIndex: 'version_name',
      key: 'version_name',
      render: (name) => name || '-',
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 180,
      render: (status: BudgetVersionStatus) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      ),
      filters: Object.entries(statusLabels).map(([value, text]) => ({ text, value })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Сумма',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 150,
      align: 'right',
      render: (amount) => `${Number(amount).toLocaleString('ru-RU')} ₽`,
      sorter: (a, b) => Number(a.total_amount) - Number(b.total_amount),
    },
    {
      title: 'CAPEX',
      dataIndex: 'total_capex',
      key: 'total_capex',
      width: 130,
      align: 'right',
      render: (amount) => `${Number(amount).toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'OPEX',
      dataIndex: 'total_opex',
      key: 'total_opex',
      width: 130,
      align: 'right',
      render: (amount) => `${Number(amount).toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Создана',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => dayjs(date).format('DD.MM.YYYY'),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
    },
    {
      title: 'Автор',
      dataIndex: 'created_by',
      key: 'created_by',
      width: 120,
      render: (author) => author || '-',
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {onView && (
            <Tooltip title="Просмотр">
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={() => onView(record)}
              />
            </Tooltip>
          )}
          {onEdit && [BudgetVersionStatus.DRAFT, BudgetVersionStatus.REVISION_REQUESTED].includes(record.status) && (
            <Tooltip title="Редактировать">
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => onEdit(record)}
              />
            </Tooltip>
          )}
          {onSubmit && record.status === BudgetVersionStatus.DRAFT && (
            <Tooltip title="Отправить на согласование">
              <Popconfirm
                title="Отправить на согласование?"
                description="После отправки редактирование будет недоступно"
                onConfirm={() => onSubmit(record.id)}
                okText="Да"
                cancelText="Нет"
              >
                <Button type="link" size="small" icon={<SendOutlined />} />
              </Popconfirm>
            </Tooltip>
          )}
          {onCopy && (
            <Tooltip title="Копировать версию">
              <Button
                type="link"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => onCopy(record)}
              />
            </Tooltip>
          )}
          {onDelete && [BudgetVersionStatus.DRAFT, BudgetVersionStatus.REJECTED].includes(record.status) && (
            <Tooltip title="Удалить">
              <Popconfirm
                title="Удалить версию?"
                description="Это действие нельзя отменить"
                onConfirm={() => onDelete(record.id)}
                okText="Да"
                cancelText="Нет"
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  const rowSelection = onSelectionChange
    ? {
        selectedRowKeys: selectedRowKeys || [],
        onChange: onSelectionChange,
        type: 'checkbox' as const,
        getCheckboxProps: () => ({
          // Можно ограничить выбор только двумя версиями
          disabled: (selectedRowKeys?.length || 0) >= 2 && !(selectedRowKeys || []).includes,
        }),
      }
    : undefined

  return (
    <Table
      columns={columns}
      dataSource={versions}
      rowKey="id"
      loading={loading}
      scroll={{ x: 1400 }}
      rowSelection={rowSelection}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `Всего: ${total}`,
      }}
    />
  )
}
