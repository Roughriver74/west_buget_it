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

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane tab="Сводка" key="summary">
          <KpiSummaryTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Цели KPI" key="goals">
          <KpiGoalsTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Шаблоны целей" key="templates">
          <KpiGoalTemplatesTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Показатели сотрудников" key="employee-kpi">
          <EmployeeKpiTab departmentId={departmentId} year={currentYear} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Назначения целей" key="assignments">
          <KpiAssignmentsTab departmentId={departmentId} year={currentYear} />
        </Tabs.TabPane>

        {/* Tasks tab removed - Tasks feature deprecated */}

        <Tabs.TabPane tab="Календарь бонусов" key="calendar">
          <KpiCalendar departmentId={departmentId} />
        </Tabs.TabPane>
      </Tabs>
    </div>
  )
}

export default KPIManagementPage
