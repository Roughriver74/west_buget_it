import { useState } from 'react'
import { Layout, Menu, theme, Space, Dropdown, Avatar, Button, Drawer } from 'antd'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  DollarOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  CalendarOutlined,
  TeamOutlined,
  BankOutlined,
  FundOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  IdcardOutlined,
  ProjectOutlined,
  MenuOutlined,
} from '@ant-design/icons'
import { useAuth } from '../../contexts/AuthContext'
import DepartmentSelector from './DepartmentSelector'
import { useBreakpoint } from '../../hooks/useBreakpoint'

const { Header, Content, Sider } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { isMobile } = useBreakpoint()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Профиль',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Настройки',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Выйти',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  // Build menu items based on user role
  const baseMenuItems = [
		{
			key: '/dashboard',
			icon: <DashboardOutlined />,
			label: <Link to='/dashboard'>Дашборд</Link>,
		},
		{
			key: '/budget',
			icon: <DollarOutlined />,
			label: <Link to='/budget'>Бюджет</Link>,
			children: [
				{
					key: '/budget/planning',
					icon: <ProjectOutlined />,
					label: <Link to='/budget/planning'>Планирование</Link>,
				},
				{
					key: '/budget/plan',
					icon: <DollarOutlined />,
					label: <Link to='/budget/plan'>Год в целом</Link>,
				},
			],
		},
		{
			key: '/expenses',
			icon: <FileTextOutlined />,
			label: <Link to='/expenses'>Заявки</Link>,
		},

		{
			key: '/payment-calendar',
			icon: <CalendarOutlined />,
			label: <Link to='/payment-calendar'>Календарь оплат</Link>,
		},

		{
			key: 'analytics-submenu',
			icon: <BarChartOutlined />,
			label: 'Аналитика',
			children: [
				{
					key: '/forecast',
					icon: <FundOutlined />,
					label: <Link to='/forecast'>Прогноз расходов</Link>,
				},
				{
					key: '/analytics',
					label: <Link to='/analytics'>Дашборд</Link>,
				},
				{
					key: '/analytics/balance',
					label: <Link to='/analytics/balance'>План-Факт-Остаток</Link>,
				},
				{
					key: '/analytics/extended',
					label: <Link to='/analytics/extended'>Расширенная аналитика</Link>,
				},
			],
		},

		{
			key: 'payroll-submenu',
			icon: <IdcardOutlined />,
			label: 'ФОТ (Зарплаты)',
			children: [
				{
					key: '/employees',
					label: <Link to='/employees'>Сотрудники</Link>,
				},
				{
					key: '/payroll/plan',
					label: <Link to='/payroll/plan'>Планирование ФОТ</Link>,
				},
				{
					key: '/payroll/actuals',
					label: <Link to='/payroll/actuals'>Фактические выплаты</Link>,
				},
				{
					key: '/payroll/kpi',
					label: <Link to='/payroll/kpi'>KPI сотрудников</Link>,
				},
				{
					key: '/kpi/analytics',
					label: <Link to='/kpi/analytics'>Аналитика КПИ</Link>,
				},
				{
					key: '/payroll/analytics',
					label: <Link to='/payroll/analytics'>Аналитика ФОТ</Link>,
				},
				{
					key: '/payroll/ndfl',
					label: <Link to='/payroll/ndfl'>Калькулятор НДФЛ</Link>,
				},
			],
		},
		{
			key: 'categories-submenu',
			icon: <BarChartOutlined />,
			label: 'Справочники',
			children: [
				{
					key: '/categories',
					icon: <DatabaseOutlined />,
					label: <Link to='/categories'>Статьи расходов</Link>,
				},
				{
					key: '/contractors',
					icon: <TeamOutlined />,
					label: <Link to='/contractors'>Контрагенты</Link>,
				},
				{
					key: '/organizations',
					icon: <BankOutlined />,
					label: <Link to='/organizations'>Организации</Link>,
				},
			],
		},
	]

  // Add admin-only menu items
  const menuItems = user?.role === 'ADMIN'
    ? [
        ...baseMenuItems,
        {
          key: '/departments',
          icon: <BankOutlined />,
          label: <Link to="/departments">Отделы</Link>,
        },
        {
          key: '/users',
          icon: <UserOutlined />,
          label: <Link to="/users">Пользователи</Link>,
        },
      ]
    : baseMenuItems

  // Render menu content (shared between Sider and Drawer)
  const renderMenu = () => (
    <Menu
      theme="dark"
      selectedKeys={[location.pathname]}
      mode="inline"
      items={menuItems}
      defaultSelectedKeys={[location.pathname]}
      onClick={() => {
        if (isMobile) {
          setMobileMenuOpen(false)
        }
      }}
    />
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
          <div
            style={{
              height: 32,
              margin: 16,
              color: 'white',
              fontSize: collapsed ? 14 : 18,
              fontWeight: 'bold',
              textAlign: 'center',
            }}
          >
            {collapsed ? 'ITB' : 'BDR'}
          </div>
          {renderMenu()}
        </Sider>
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          title={
            <div style={{ color: 'white', fontSize: 18, fontWeight: 'bold' }}>
              BDR
            </div>
          }
          placement="left"
          onClose={() => setMobileMenuOpen(false)}
          open={mobileMenuOpen}
          styles={{
            body: { padding: 0, background: '#001529' },
            header: { background: '#001529', borderBottom: '1px solid #1d3a5f' },
          }}
          width={250}
        >
          {renderMenu()}
        </Drawer>
      )}

      <Layout>
        <Header
          style={{
            padding: isMobile ? '0 16px' : '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: isMobile ? 'auto' : 64,
            lineHeight: isMobile ? 'normal' : '64px',
          }}
        >
          <Space>
            {/* Mobile menu button */}
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileMenuOpen(true)}
                style={{ fontSize: 20 }}
              />
            )}
            <div
              style={{
                fontSize: isMobile ? 16 : 20,
                fontWeight: 500,
                whiteSpace: 'nowrap',
              }}
            >
              {isMobile ? 'BDR' : 'IT Budget Manager'}
            </div>
          </Space>

          <Space size={isMobile ? 'small' : 'large'} wrap>
            {!isMobile && <DepartmentSelector />}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" style={{ height: 'auto', padding: '4px 8px' }}>
                <Space size="small">
                  <Avatar size="small" icon={<UserOutlined />} />
                  {!isMobile && <span>{user?.full_name || user?.username}</span>}
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: isMobile ? '12px 8px 0' : '24px 16px 0' }}>
          <div
            style={{
              padding: isMobile ? 16 : 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {isMobile && (
              <div style={{ marginBottom: 16 }}>
                <DepartmentSelector />
              </div>
            )}
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
