/**
 * React Query hooks for Budget Planning Module
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import {
  scenariosApi,
  versionsApi,
  planDetailsApi,
  calculatorApi,
  approvalLogApi,
} from '@/api/budgetPlanning'
import type {
  BudgetScenarioCreate,
  BudgetScenarioUpdate,
  BudgetScenarioFilters,
  BudgetVersionCreate,
  BudgetVersionUpdate,
  BudgetVersionFilters,
  BudgetPlanDetailCreate,
  BudgetPlanDetailUpdate,
  BudgetApprovalLogCreate,
  CalculateByAverageRequest,
  CalculateByGrowthRequest,
  CalculateByDriverRequest,
} from '@/types/budgetPlanning'

// ============================================================================
// Query Keys
// ============================================================================

export const budgetPlanningKeys = {
  all: ['budgetPlanning'] as const,
  scenarios: () => [...budgetPlanningKeys.all, 'scenarios'] as const,
  scenariosList: (filters?: BudgetScenarioFilters) => [...budgetPlanningKeys.scenarios(), { filters }] as const,
  scenario: (id: number) => [...budgetPlanningKeys.scenarios(), id] as const,
  versions: () => [...budgetPlanningKeys.all, 'versions'] as const,
  versionsList: (filters?: BudgetVersionFilters) => [...budgetPlanningKeys.versions(), { filters }] as const,
  version: (id: number) => [...budgetPlanningKeys.versions(), id] as const,
  versionWithDetails: (id: number) => [...budgetPlanningKeys.versions(), id, 'details'] as const,
  planDetails: (versionId: number) => [...budgetPlanningKeys.all, 'planDetails', versionId] as const,
  approvalLogs: (versionId: number) => [...budgetPlanningKeys.all, 'approvalLogs', versionId] as const,
  baseline: (categoryId: number, year: number, departmentId: number) =>
    [...budgetPlanningKeys.all, 'baseline', categoryId, year, departmentId] as const,
}

// ============================================================================
// Scenarios Hooks
// ============================================================================

export const useBudgetScenarios = (filters?: BudgetScenarioFilters) => {
  return useQuery({
    queryKey: budgetPlanningKeys.scenariosList(filters),
    queryFn: () => scenariosApi.getAll(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useBudgetScenario = (id: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.scenario(id),
    queryFn: () => scenariosApi.getById(id),
    enabled: !!id,
  })
}

export const useCreateScenario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BudgetScenarioCreate) => scenariosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.scenarios() })
      message.success('Сценарий успешно создан')
    },
    onError: () => {
      message.error('Ошибка при создании сценария')
    },
  })
}

export const useUpdateScenario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: BudgetScenarioUpdate }) =>
      scenariosApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.scenarios() })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.scenario(variables.id) })
      message.success('Сценарий успешно обновлен')
    },
    onError: () => {
      message.error('Ошибка при обновлении сценария')
    },
  })
}

export const useDeleteScenario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => scenariosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.scenarios() })
      message.success('Сценарий успешно удален')
    },
    onError: () => {
      message.error('Ошибка при удалении сценария')
    },
  })
}

// ============================================================================
// Versions Hooks
// ============================================================================

export const useBudgetVersions = (filters?: BudgetVersionFilters) => {
  return useQuery({
    queryKey: budgetPlanningKeys.versionsList(filters),
    queryFn: () => versionsApi.getAll(filters),
    staleTime: 5 * 60 * 1000,
  })
}

export const useBudgetVersion = (id: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.version(id),
    queryFn: () => versionsApi.getById(id),
    enabled: !!id,
  })
}

export const useBudgetVersionWithDetails = (id: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.versionWithDetails(id),
    queryFn: () => versionsApi.getWithDetails(id),
    enabled: !!id,
  })
}

export const useCreateVersion = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BudgetVersionCreate) => versionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      message.success('Версия бюджета успешно создана')
    },
    onError: () => {
      message.error('Ошибка при создании версии')
    },
  })
}

export const useUpdateVersion = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: BudgetVersionUpdate }) =>
      versionsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.version(variables.id) })
      message.success('Версия бюджета обновлена')
    },
    onError: () => {
      message.error('Ошибка при обновлении версии')
    },
  })
}

export const useDeleteVersion = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => versionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      message.success('Версия бюджета удалена')
    },
    onError: () => {
      message.error('Ошибка при удалении версии')
    },
  })
}

export const useSubmitVersion = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => versionsApi.submit(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.version(id) })
      message.success('Версия отправлена на согласование')
    },
    onError: () => {
      message.error('Ошибка при отправке версии')
    },
  })
}

// ============================================================================
// Plan Details Hooks
// ============================================================================

export const usePlanDetails = (versionId: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.planDetails(versionId),
    queryFn: () => planDetailsApi.getByVersion(versionId),
    enabled: !!versionId,
  })
}

export const useCreatePlanDetail = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BudgetPlanDetailCreate) => planDetailsApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.planDetails(data.version_id) })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      message.success('Строка бюджета добавлена')
    },
    onError: () => {
      message.error('Ошибка при добавлении строки')
    },
  })
}

export const useUpdatePlanDetail = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: BudgetPlanDetailUpdate }) =>
      planDetailsApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.planDetails(data.version_id) })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      message.success('Строка бюджета обновлена')
    },
    onError: () => {
      message.error('Ошибка при обновлении строки')
    },
  })
}

export const useDeletePlanDetail = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, versionId }: { id: number; versionId: number }) =>
      planDetailsApi.delete(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.planDetails(variables.versionId) })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      message.success('Строка бюджета удалена')
    },
    onError: () => {
      message.error('Ошибка при удалении строки')
    },
  })
}

// ============================================================================
// Calculator Hooks
// ============================================================================

export const useCalculateByAverage = () => {
  return useMutation({
    mutationFn: (request: CalculateByAverageRequest) =>
      calculatorApi.calculateByAverage(request),
    onError: () => {
      message.error('Ошибка при расчете по среднему')
    },
  })
}

export const useCalculateByGrowth = () => {
  return useMutation({
    mutationFn: (request: CalculateByGrowthRequest) =>
      calculatorApi.calculateByGrowth(request),
    onError: () => {
      message.error('Ошибка при расчете с учетом роста')
    },
  })
}

export const useCalculateByDriver = () => {
  return useMutation({
    mutationFn: (request: CalculateByDriverRequest) =>
      calculatorApi.calculateByDriver(request),
    onError: () => {
      message.error('Ошибка при расчете по драйверу')
    },
  })
}

export const useBaseline = (categoryId: number, year: number, departmentId: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.baseline(categoryId, year, departmentId),
    queryFn: () => calculatorApi.getBaseline(categoryId, year, departmentId),
    enabled: !!categoryId && !!year && !!departmentId,
  })
}

// ============================================================================
// Approval Log Hooks
// ============================================================================

export const useApprovalLogs = (versionId: number) => {
  return useQuery({
    queryKey: budgetPlanningKeys.approvalLogs(versionId),
    queryFn: () => approvalLogApi.getByVersion(versionId),
    enabled: !!versionId,
  })
}

export const useCreateApprovalLog = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: BudgetApprovalLogCreate) => approvalLogApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.approvalLogs(data.version_id) })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.versions() })
      queryClient.invalidateQueries({ queryKey: budgetPlanningKeys.version(data.version_id) })
      message.success('Решение по согласованию сохранено')
    },
    onError: () => {
      message.error('Ошибка при сохранении решения')
    },
  })
}
