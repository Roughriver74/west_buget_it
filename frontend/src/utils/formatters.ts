import { ExpenseStatus } from '../types'

// Mapping для статусов на русский язык
export const expenseStatusLabels: Record<ExpenseStatus, string> = {
  [ExpenseStatus.DRAFT]: 'Черновик',
  [ExpenseStatus.PENDING]: 'К оплате',
  [ExpenseStatus.PAID]: 'Оплачена',
  [ExpenseStatus.REJECTED]: 'Отклонена',
  [ExpenseStatus.CLOSED]: 'Закрыта',
}

// Функция для получения русского названия статуса
export const getExpenseStatusLabel = (status: ExpenseStatus): string => {
  return expenseStatusLabels[status] || status
}

// Цвета для статусов
export const expenseStatusColors: Record<ExpenseStatus, string> = {
  [ExpenseStatus.DRAFT]: 'default',
  [ExpenseStatus.PENDING]: 'warning',
  [ExpenseStatus.PAID]: 'success',
  [ExpenseStatus.REJECTED]: 'error',
  [ExpenseStatus.CLOSED]: 'default',
}

// Функция для получения цвета статуса
export const getExpenseStatusColor = (status: ExpenseStatus): string => {
  return expenseStatusColors[status] || 'default'
}

// Функция форматирования валюты
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value)
}
