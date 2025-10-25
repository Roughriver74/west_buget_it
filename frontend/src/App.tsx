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
