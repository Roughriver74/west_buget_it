import { useState } from 'react'
import { Tabs, Typography } from 'antd'
import dayjs from 'dayjs'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { KpiSummaryTab } from '@/components/kpi/KpiSummaryTab'
import { KpiGoalsTab } from '@/components/kpi/KpiGoalsTab'
import { KpiGoalTemplatesTab } from '@/components/kpi/KpiGoalTemplatesTab'
import { EmployeeKpiTab } from '@/components/kpi/EmployeeKpiTab'
import { KpiAssignmentsTab } from '@/components/kpi/KpiAssignmentsTab'
import { KpiCalendar } from '@/components/kpi/KpiCalendar'
import { KpiDashboard } from '@/components/kpi/KpiDashboard'
// KpiAllTasksTab removed - Tasks feature deprecated

const { Title } = Typography

const KPIManagementPage = () => {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('summary')

  const departmentId = selectedDepartment?.id ?? user?.department_id ?? undefined
  const currentYear = dayjs().year()

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>
        KPI сотрудников
      </Title>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'dashboard',
            label: '📊 Dashboard',
            children: <KpiDashboard departmentId={departmentId} />,
          },
          {
            key: 'summary',
            label: 'Сводка',
            children: <KpiSummaryTab departmentId={departmentId} />,
          },
          {
            key: 'goals',
            label: 'Цели KPI',
            children: <KpiGoalsTab departmentId={departmentId} />,
          },
          {
            key: 'templates',
            label: 'Шаблоны целей',
            children: <KpiGoalTemplatesTab departmentId={departmentId} />,
          },
          {
            key: 'employee-kpi',
            label: 'Показатели сотрудников',
            children: <EmployeeKpiTab departmentId={departmentId} year={currentYear} />,
          },
          {
            key: 'assignments',
            label: 'Назначения целей',
            children: <KpiAssignmentsTab departmentId={departmentId} year={currentYear} />,
          },
          {
            key: 'calendar',
            label: 'Календарь бонусов',
            children: <KpiCalendar departmentId={departmentId} />,
          },
        ]}
      />
    </div>
  )
}

export default KPIManagementPage
