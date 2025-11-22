/**
 * ModulesContext - Global module access control
 *
 * Provides:
 * - List of enabled modules for current user's organization
 * - Helper functions to check module access
 * - Module loading state
 */

import React, { createContext, useContext, ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { EnabledModulesResponse, EnabledModuleInfo, ModuleCode } from '@/types/module'
import * as modulesApi from '@/api/modules'

interface ModulesContextType {
  // Data
  modules: EnabledModuleInfo[]
  organizationId?: number
  organizationName?: string

  // Loading state
  isLoading: boolean
  isError: boolean
  error: Error | null

  // Helper functions
  hasModule: (moduleCode: ModuleCode | string) => boolean
  getModule: (moduleCode: ModuleCode | string) => EnabledModuleInfo | undefined
  isModuleExpired: (moduleCode: ModuleCode | string) => boolean

  // Refetch
  refetch: () => void
}

const ModulesContext = createContext<ModulesContextType | undefined>(undefined)

interface ModulesProviderProps {
  children: ReactNode
}

export const ModulesProvider: React.FC<ModulesProviderProps> = ({ children }) => {
  // Fetch enabled modules for current user's organization
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<EnabledModulesResponse, Error>({
    queryKey: ['modules', 'enabled', 'my'],
    queryFn: () => modulesApi.getMyEnabledModules({ include_expired: false }),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (previously cacheTime)
    refetchOnWindowFocus: false,
  })

  // Helper: Check if module is enabled
  const hasModule = (moduleCode: ModuleCode | string): boolean => {
    if (!data?.modules) return false
    return data.modules.some((m) => m.code === moduleCode && !m.is_expired)
  }

  // Helper: Get module info
  const getModule = (moduleCode: ModuleCode | string): EnabledModuleInfo | undefined => {
    if (!data?.modules) return undefined
    return data.modules.find((m) => m.code === moduleCode)
  }

  // Helper: Check if module is expired
  const isModuleExpired = (moduleCode: ModuleCode | string): boolean => {
    const module = getModule(moduleCode)
    return module?.is_expired ?? true
  }

  const value: ModulesContextType = {
    modules: data?.modules ?? [],
    organizationId: data?.organization_id,
    organizationName: data?.organization_name,
    isLoading,
    isError,
    error: error ?? null,
    hasModule,
    getModule,
    isModuleExpired,
    refetch,
  }

  return <ModulesContext.Provider value={value}>{children}</ModulesContext.Provider>
}

/**
 * Hook to access modules context
 *
 * @example
 * ```tsx
 * const { hasModule, isLoading } = useModules()
 *
 * if (hasModule('AI_FORECAST')) {
 *   // Show AI features
 * }
 * ```
 */
export const useModules = (): ModulesContextType => {
  const context = useContext(ModulesContext)
  if (context === undefined) {
    throw new Error('useModules must be used within a ModulesProvider')
  }
  return context
}

/**
 * Hook to check if a specific module is enabled
 *
 * @example
 * ```tsx
 * const hasAI = useHasModule('AI_FORECAST')
 * if (hasAI) {
 *   // Show AI-powered features
 * }
 * ```
 */
export const useHasModule = (moduleCode: ModuleCode | string): boolean => {
  const { hasModule } = useModules()
  return hasModule(moduleCode)
}

/**
 * Hook to get module info
 *
 * @example
 * ```tsx
 * const aiModule = useModuleInfo('AI_FORECAST')
 * if (aiModule) {
 *   console.log('AI module expires at:', aiModule.expires_at)
 * }
 * ```
 */
export const useModuleInfo = (moduleCode: ModuleCode | string): EnabledModuleInfo | undefined => {
  const { getModule } = useModules()
  return getModule(moduleCode)
}
