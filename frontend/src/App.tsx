import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/common/AppLayout'
import DashboardPage from './pages/DashboardPage'
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

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/budget" element={<BudgetOverviewPage />} />
          <Route path="/expenses" element={<ExpensesPage />} />
          <Route path="/budget/plan" element={<BudgetPlanPage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/contractors" element={<ContractorsPage />} />
          <Route path="/contractors/:id" element={<ContractorDetailPage />} />
          <Route path="/organizations" element={<OrganizationsPage />} />
          <Route path="/organizations/:id" element={<OrganizationDetailPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/analytics/balance" element={<BalanceAnalyticsPage />} />
          <Route path="/payment-calendar" element={<PaymentCalendarPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
        </Routes>
      </AppLayout>
    </Router>
  )
}

export default App
