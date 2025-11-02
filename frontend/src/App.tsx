import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { DepartmentProvider } from './contexts/DepartmentContext'
import AppLayout from './components/common/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoadingState from './components/common/LoadingState'

// Public pages - load immediately
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UnauthorizedPage from './pages/UnauthorizedPage'

// Core pages - load immediately (frequently accessed)
import DashboardPage from './pages/DashboardPage'

// Lazy-loaded pages (code splitting by module)

// Budget module
const BudgetOverviewPage = lazy(() => import('./pages/BudgetOverviewPage'))
const BudgetPlanPage = lazy(() => import('./pages/BudgetPlanPage'))
const BudgetPlanningPage = lazy(() => import('./pages/BudgetPlanningPage'))
const ExpensesPage = lazy(() => import('./pages/ExpensesPage'))

// Analytics module
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const BalanceAnalyticsPage = lazy(() => import('./pages/BalanceAnalyticsPage'))
const ExtendedAnalyticsPage = lazy(() => import('./pages/ExtendedAnalyticsPage'))
const PaymentCalendarPage = lazy(() => import('./pages/PaymentCalendarPage'))
const ForecastPage = lazy(() => import('./pages/ForecastPage'))
const CustomDashboardPage = lazy(() => import('./pages/CustomDashboardPage'))
const BudgetIncomeStatementPage = lazy(() => import('./pages/BudgetIncomeStatementPage'))
const CustomerMetricsAnalyticsPage = lazy(() => import('./pages/CustomerMetricsAnalyticsPage'))

// Reference data module
const CategoriesPage = lazy(() => import('./pages/CategoriesPage'))
const ContractorsPage = lazy(() => import('./pages/ContractorsPage'))
const OrganizationsPage = lazy(() => import('./pages/OrganizationsPage'))
const ContractorDetailPage = lazy(() => import('./pages/ContractorDetailPage'))
const OrganizationDetailPage = lazy(() => import('./pages/OrganizationDetailPage'))

// Admin module
const DepartmentsPage = lazy(() => import('./pages/DepartmentsPage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))

// Payroll module
const EmployeesPage = lazy(() => import('./pages/EmployeesPage'))
const EmployeeDetailPage = lazy(() => import('./pages/EmployeeDetailPage'))
const PayrollPlanPage = lazy(() => import('./pages/PayrollPlanPage'))
const PayrollActualsPage = lazy(() => import('./pages/PayrollActualsPage'))
const PayrollAnalyticsPage = lazy(() => import('./pages/PayrollAnalyticsPage'))
const KpiManagementPage = lazy(() => import('./pages/KpiManagementPage'))
const KPIAnalyticsPage = lazy(() => import('./pages/KPIAnalyticsPage'))
const NDFLCalculatorPage = lazy(() => import('./pages/NDFLCalculatorPage'))

// Revenue module
const RevenueDashboardPage = lazy(() => import('./pages/RevenueDashboardPage'))
const RevenueStreamsPage = lazy(() => import('./pages/RevenueStreamsPage'))
const RevenueCategoriesPage = lazy(() => import('./pages/RevenueCategoriesPage'))
const RevenueActualsPage = lazy(() => import('./pages/RevenueActualsPage'))
const RevenuePlanningPage = lazy(() => import('./pages/RevenuePlanningPage'))
const RevenuePlanDetailsPage = lazy(() => import('./pages/RevenuePlanDetailsPage'))
const CustomerMetricsPage = lazy(() => import('./pages/CustomerMetricsPage'))
const SeasonalityPage = lazy(() => import('./pages/SeasonalityPage'))
const RevenueAnalyticsPage = lazy(() => import('./pages/RevenueAnalyticsPage'))

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Protected routes */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <DepartmentProvider>
                    <AppLayout>
                      <Suspense fallback={<LoadingState />}>
                        <Routes>
                          <Route path="/" element={<Navigate to="/dashboard" replace />} />
                          <Route path="/dashboard" element={<DashboardPage />} />
                          <Route path="/dashboard/custom" element={<CustomDashboardPage />} />
                          <Route path="/budget" element={<BudgetOverviewPage />} />
                          <Route path="/expenses" element={<ExpensesPage />} />

                        {/* Budget planning - Accountant and Admin only */}
                        <Route
                          path="/budget/plan"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <BudgetPlanPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Budget planning (multi-year) - Admin and Manager only */}
                        <Route
                          path="/budget/planning"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <BudgetPlanningPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Reference data - Accountant and Admin only */}
                        <Route
                          path="/categories"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <CategoriesPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/contractors"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <ContractorsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/contractors/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <ContractorDetailPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/organizations"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <OrganizationsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/organizations/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <OrganizationDetailPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Departments - Admin only */}
                        <Route
                          path="/departments"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN']}>
                              <DepartmentsPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Users - Admin only */}
                        <Route
                          path="/users"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN']}>
                              <UsersPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Payroll (FOT) - Admin and Manager only */}
                        <Route
                          path="/employees/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <EmployeeDetailPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/employees"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <EmployeesPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/plan"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <PayrollPlanPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/actuals"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <PayrollActualsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/kpi"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <KpiManagementPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/analytics"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <PayrollAnalyticsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/ndfl"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                              <NDFLCalculatorPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/kpi/analytics"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <KPIAnalyticsPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Revenue - all authenticated users */}
                        <Route path="/revenue/dashboard" element={<RevenueDashboardPage />} />
                        <Route path="/revenue/streams" element={<RevenueStreamsPage />} />
                        <Route path="/revenue/categories" element={<RevenueCategoriesPage />} />
                        <Route path="/revenue/actuals" element={<RevenueActualsPage />} />
                        <Route path="/revenue/customer-metrics" element={<CustomerMetricsPage />} />
                        <Route path="/revenue/seasonality" element={<SeasonalityPage />} />
                        <Route path="/revenue/analytics" element={<RevenueAnalyticsPage />} />

                        {/* Revenue Planning - Admin and Manager only */}
                        <Route
                          path="/revenue/planning"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <RevenuePlanningPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/revenue/planning/:planId"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <RevenuePlanDetailsPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Analytics - all authenticated users */}
                        <Route path="/analytics" element={<AnalyticsPage />} />
                        <Route path="/analytics/balance" element={<BalanceAnalyticsPage />} />
                        <Route path="/analytics/extended" element={<ExtendedAnalyticsPage />} />
                        <Route path="/analytics/budget-income-statement" element={<BudgetIncomeStatementPage />} />
                        <Route path="/analytics/customer-metrics" element={<CustomerMetricsAnalyticsPage />} />
                        <Route path="/payment-calendar" element={<PaymentCalendarPage />} />
                        <Route path="/forecast" element={<ForecastPage />} />
                        </Routes>
                      </Suspense>
                    </AppLayout>
                  </DepartmentProvider>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  )
}

export default App
