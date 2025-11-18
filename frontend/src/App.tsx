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

// Founder module
const FounderDashboardPage = lazy(() => import('./pages/FounderDashboardPage'))

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
const RevenueAnalyticsExtendedPage = lazy(() => import('./pages/RevenueAnalyticsExtendedPage'))
const UnifiedFinancialDashboardPage = lazy(() => import('./pages/UnifiedFinancialDashboardPage'))

// Reference data module
const CategoriesPage = lazy(() => import('./pages/CategoriesPage'))
const ContractorsPage = lazy(() => import('./pages/ContractorsPage'))
const OrganizationsPage = lazy(() => import('./pages/OrganizationsPage'))
const ContractorDetailPage = lazy(() => import('./pages/ContractorDetailPage'))
const OrganizationDetailPage = lazy(() => import('./pages/OrganizationDetailPage'))
const BusinessOperationMappingsPage = lazy(() => import('./pages/BusinessOperationMappingsPage'))
const TaxRatesPage = lazy(() => import('./pages/TaxRatesPage'))

// Admin module
const DepartmentsPage = lazy(() => import('./pages/DepartmentsPage'))
const UsersPage = lazy(() => import('./pages/UsersPage'))
// API Tokens now use drawer component instead of full page
// const ApiTokensPage = lazy(() => import('./pages/ApiTokensPage'))

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

// Bank Transactions module
const BankTransactionsPage = lazy(() => import('./pages/BankTransactionsPage'))
const BankTransactionsAnalyticsPage = lazy(() => import('./pages/BankTransactionsAnalyticsPage'))

// Credit Portfolio module
const CreditPortfolioPage = lazy(() => import('./pages/CreditPortfolioPage'))
const CreditPortfolioKPIPage = lazy(() => import('./pages/CreditPortfolioKPIPage'))
const CreditPortfolioCashFlowPage = lazy(() => import('./pages/CreditPortfolioCashFlowPage'))
const CreditPortfolioContractsPage = lazy(() => import('./pages/CreditPortfolioContractsPage'))
const CreditPortfolioComparePage = lazy(() => import('./pages/CreditPortfolioComparePage'))
const CreditPortfolioAnalyticsPage = lazy(() => import('./pages/CreditPortfolioAnalyticsPage'))

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

                          {/* Founder dashboard - FOUNDER and ADMIN only */}
                          <Route
                            path="/founder/dashboard"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'FOUNDER']}>
                                <FounderDashboardPage />
                              </ProtectedRoute>
                            }
                          />

                          <Route path="/budget" element={<BudgetOverviewPage />} />
                          <Route path="/expenses" element={<ExpensesPage />} />

                          {/* Bank Transactions - All authenticated users (filtered by department) */}
                          <Route
                            path="/bank-transactions"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'FOUNDER', 'MANAGER', 'USER']}>
                                <BankTransactionsPage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/bank-transactions/analytics"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'FOUNDER', 'MANAGER', 'USER']}>
                                <BankTransactionsAnalyticsPage />
                              </ProtectedRoute>
                            }
                          />

                          {/* Credit Portfolio - MANAGER, ADMIN, ACCOUNTANT only */}
                          <Route
                            path="/credit-portfolio"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioPage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/credit-portfolio/kpi"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioKPIPage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/credit-portfolio/cash-flow"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioCashFlowPage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/credit-portfolio/contracts"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioContractsPage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/credit-portfolio/compare"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioComparePage />
                              </ProtectedRoute>
                            }
                          />
                          <Route
                            path="/credit-portfolio/analytics"
                            element={
                              <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT']}>
                                <CreditPortfolioAnalyticsPage />
                              </ProtectedRoute>
                            }
                          />

                        {/* Budget planning - All authenticated users (filtered by department) */}
                        <Route
                          path="/budget/plan"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER', 'ACCOUNTANT']}>
                              <BudgetPlanPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Budget planning (multi-year) - All authenticated users (filtered by department) */}
                        <Route
                          path="/budget/planning"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <BudgetPlanningPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Reference data - All authenticated users can access (filtered by department) */}
                        <Route
                          path="/categories"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT', 'MANAGER', 'USER']}>
                              <CategoriesPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/contractors"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT', 'MANAGER', 'USER']}>
                              <ContractorsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/contractors/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT', 'MANAGER', 'USER']}>
                              <ContractorDetailPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/organizations"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT', 'MANAGER', 'USER']}>
                              <OrganizationsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/organizations/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT', 'MANAGER', 'USER']}>
                              <OrganizationDetailPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/references/tax-rates"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'ACCOUNTANT']}>
                              <TaxRatesPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Business Operation Mappings - ADMIN and MANAGER only */}
                        <Route
                          path="/business-operation-mappings"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
                              <BusinessOperationMappingsPage />
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

                        {/* API Tokens - Now using drawer in AppLayout instead of full page */}
                        {/* <Route
                          path="/api-tokens"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN']}>
                              <ApiTokensPage />
                            </ProtectedRoute>
                          }
                        /> */}

                        {/* Payroll (FOT) - All authenticated users (filtered by department) */}
                        <Route
                          path="/employees/:id"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <EmployeeDetailPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/employees"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <EmployeesPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/plan"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <PayrollPlanPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/actuals"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <PayrollActualsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/kpi"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <KpiManagementPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/analytics"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <PayrollAnalyticsPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/payroll/ndfl"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'ACCOUNTANT', 'USER']}>
                              <NDFLCalculatorPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/kpi/analytics"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
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

                        {/* Revenue Planning - All authenticated users (filtered by department) */}
                        <Route
                          path="/revenue/planning"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
                              <RevenuePlanningPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/revenue/planning/:planId"
                          element={
                            <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'USER']}>
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
                        <Route path="/analytics/revenue-extended" element={<RevenueAnalyticsExtendedPage />} />
                        <Route path="/analytics/unified-dashboard" element={<UnifiedFinancialDashboardPage />} />
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
