import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import AppLayout from './components/common/AppLayout'
import DashboardPage from './pages/DashboardPage'
import ExpensesPage from './pages/ExpensesPage'
import BudgetOverviewPage from './pages/BudgetOverviewPage'
import BudgetPlanPage from './pages/BudgetPlanPage'
import CategoriesPage from './pages/CategoriesPage'
import AnalyticsPage from './pages/AnalyticsPage'
import BalanceAnalyticsPage from './pages/BalanceAnalyticsPage'

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
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/analytics/balance" element={<BalanceAnalyticsPage />} />
        </Routes>
      </AppLayout>
    </Router>
  )
}

export default App
