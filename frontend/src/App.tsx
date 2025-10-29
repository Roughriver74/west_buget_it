import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { DepartmentProvider } from './contexts/DepartmentContext'
import AppLayout from './components/common/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UnauthorizedPage from './pages/UnauthorizedPage'
import DashboardPage from './pages/DashboardPage'
import CustomDashboardPage from './pages/CustomDashboardPage'
import ExpensesPage from './pages/ExpensesPage'
import BudgetOverviewPage from './pages/BudgetOverviewPage'
import BudgetPlanPage from './pages/BudgetPlanPage'
import CategoriesPage from './pages/CategoriesPage'
import ContractorsPage from './pages/ContractorsPage'
import OrganizationsPage from './pages/OrganizationsPage'
import ContractorDetailPage from './pages/ContractorDetailPage'
import OrganizationDetailPage from './pages/OrganizationDetailPage'
import AnalyticsPage from './pages/AnalyticsPage'
import BalanceAnalyticsPage from './pages/BalanceAnalyticsPage'
import PaymentCalendarPage from './pages/PaymentCalendarPage'
import ForecastPage from './pages/ForecastPage'
import DepartmentsPage from './pages/DepartmentsPage'
import UsersPage from './pages/UsersPage'
import EmployeesPage from './pages/EmployeesPage'
import EmployeeDetailPage from './pages/EmployeeDetailPage'
import PayrollPlanPage from './pages/PayrollPlanPage'
import PayrollAnalyticsPage from './pages/PayrollAnalyticsPage'
import KpiManagementPage from './pages/KpiManagementPage'
import KPIAnalyticsPage from './pages/KPIAnalyticsPage'
import BudgetPlanningPage from './pages/BudgetPlanningPage'
import PayrollActualsPage from './pages/PayrollActualsPage'
import NDFLCalculatorPage from './pages/NDFLCalculatorPage'

function App() {
  return (
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

                    {/* Analytics - all authenticated users */}
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/analytics/balance" element={<BalanceAnalyticsPage />} />
                    <Route path="/payment-calendar" element={<PaymentCalendarPage />} />
                    <Route path="/forecast" element={<ForecastPage />} />
                    </Routes>
                  </AppLayout>
                </DepartmentProvider>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
