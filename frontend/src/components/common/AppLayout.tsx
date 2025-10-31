import { useState, useEffect } from 'react'
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
  RiseOutlined,
  DollarCircleOutlined,
} from '@ant-design/icons'
import { useAuth } from '../../contexts/AuthContext'
import DepartmentSelector from './DepartmentSelector'

const { Header, Content, Sider } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)

    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileDrawerOpen(false)
  }, [location.pathname])

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
			key: 'revenue-submenu',
			icon: <RiseOutlined />,
			label: 'Доходы',
			children: [
				{
					key: '/revenue/dashboard',
					icon: <DashboardOutlined />,
					label: <Link to='/revenue/dashboard'>Дашборд</Link>,
				},
				{
					key: '/revenue/streams',
					icon: <FundOutlined />,
					label: <Link to='/revenue/streams'>Потоки доходов</Link>,
				},
				{
					key: '/revenue/categories',
					icon: <DatabaseOutlined />,
					label: <Link to='/revenue/categories'>Категории доходов</Link>,
				},
				{
					key: '/revenue/actuals',
					icon: <DollarCircleOutlined />,
					label: <Link to='/revenue/actuals'>Фактические доходы</Link>,
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

  // Menu content component (reused for both Sider and Drawer)
  const menuContent = (
    <>
      <div
        style={{
          height: 32,
          margin: 16,
          color: 'white',
          fontSize: collapsed && !isMobile ? 14 : 18,
          fontWeight: 'bold',
          textAlign: 'center',
        }}
      >
        {collapsed && !isMobile ? 'ITB' : 'BDR'}
      </div>
      <Menu
        theme="dark"
        selectedKeys={[location.pathname]}
        mode="inline"
        items={menuItems}
        defaultSelectedKeys={[location.pathname]}
      />
    </>
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop Sider */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          breakpoint="md"
          collapsedWidth={80}
        >
          {menuContent}
        </Sider>
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          placement="left"
          onClose={() => setMobileDrawerOpen(false)}
          open={mobileDrawerOpen}
          styles={{ body: { padding: 0, background: '#001529' } }}
          width={250}
        >
          {menuContent}
        </Drawer>
      )}

      <Layout>
        <Header
          style={{
            padding: isMobile ? '0 12px' : '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Space>
            {/* Mobile menu button */}
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileDrawerOpen(true)}
                style={{ fontSize: 20 }}
              />
            )}
            <div style={{ fontSize: isMobile ? 16 : 20, fontWeight: 500 }}>
              {isMobile ? 'BDR' : 'IT Budget Manager'}
            </div>
          </Space>

          <Space size={isMobile ? 'small' : 'large'}>
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
              padding: isMobile ? 12 : 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
