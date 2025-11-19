/**
 * ModuleGate - Conditional rendering based on module access
 *
 * Wraps components/routes to show/hide based on whether a module is enabled
 */

import React, { ReactNode } from 'react'
import { Alert, Spin } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { useModules } from '@/contexts/ModulesContext'
import type { ModuleCode } from '@/types/module'

interface ModuleGateProps {
  /**
   * Module code required to access children
   */
  moduleCode: ModuleCode | string

  /**
   * Content to render when module is enabled
   */
  children: ReactNode

  /**
   * Custom fallback content when module is not enabled
   * If not provided, shows default "Module not enabled" message
   */
  fallback?: ReactNode

  /**
   * Whether to show loading spinner while checking module access
   * Default: true
   */
  showLoading?: boolean

  /**
   * Custom loading component
   */
  loadingComponent?: ReactNode

  /**
   * Whether to show error if module check fails
   * Default: true
   */
  showError?: boolean
}

/**
 * ModuleGate component
 *
 * @example
 * ```tsx
 * // Simple usage - hide content if module not enabled
 * <ModuleGate moduleCode="AI_FORECAST">
 *   <BankTransactionsPage />
 * </ModuleGate>
 *
 * // With custom fallback
 * <ModuleGate
 *   moduleCode="CREDIT_PORTFOLIO"
 *   fallback={<div>Upgrade to access Credit Portfolio</div>}
 * >
 *   <CreditPortfolioPage />
 * </ModuleGate>
 * ```
 */
export const ModuleGate: React.FC<ModuleGateProps> = ({
  moduleCode,
  children,
  fallback,
  showLoading = true,
  loadingComponent,
  showError = true,
}) => {
  const { hasModule, getModule, isLoading, isError } = useModules()

  // Loading state
  if (isLoading && showLoading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>
    }

    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 200,
        }}
      >
        <Spin size="large" tip="Проверка доступа к модулю..." />
      </div>
    )
  }

  // Error state
  if (isError && showError) {
    return (
      <Alert
        message="Ошибка проверки доступа"
        description="Не удалось проверить доступ к модулю. Попробуйте перезагрузить страницу."
        type="error"
        showIcon
      />
    )
  }

  // Check if module is enabled
  // TEMPORARILY DISABLED: Module system is disabled - always allow access
  const moduleEnabled = true // TEMPORARILY DISABLED: hasModule(moduleCode)

  if (!moduleEnabled) {
    // Show custom fallback if provided
    if (fallback) {
      return <>{fallback}</>
    }

    // Default fallback message
    const module = getModule(moduleCode)
    const moduleName = module?.name ?? moduleCode

    return (
      <Alert
        message={`Модуль недоступен: ${moduleName}`}
        description={
          module?.is_expired
            ? 'Срок действия модуля истек. Обратитесь к администратору для продления.'
            : 'Модуль не включен для вашей организации. Обратитесь к администратору для активации.'
        }
        type="warning"
        showIcon
        icon={<LockOutlined />}
        style={{ margin: 24 }}
      />
    )
  }

  // Module is enabled - render children
  return <>{children}</>
}

/**
 * ModuleGuard - Higher-order component wrapper for ModuleGate
 *
 * @example
 * ```tsx
 * const ProtectedComponent = ModuleGuard(MyComponent, 'AI_FORECAST')
 * ```
 */
export const ModuleGuard = <P extends object>(
  Component: React.ComponentType<P>,
  moduleCode: ModuleCode | string,
  options?: Omit<ModuleGateProps, 'moduleCode' | 'children'>
) => {
  const WrappedComponent: React.FC<P> = (props) => (
    <ModuleGate moduleCode={moduleCode} {...options}>
      <Component {...props} />
    </ModuleGate>
  )

  WrappedComponent.displayName = `ModuleGuard(${Component.displayName || Component.name || 'Component'})`

  return WrappedComponent
}
