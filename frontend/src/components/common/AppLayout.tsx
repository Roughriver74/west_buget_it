import { useState, useEffect } from 'react'
import {
	Layout,
	Menu,
	Space,
	Dropdown,
	Avatar,
	Button,
	Drawer,
	Tooltip,
} from 'antd'
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
	LineChartOutlined,
	BulbOutlined,
	BulbFilled,
	KeyOutlined,
	TrophyOutlined,
	CreditCardOutlined,
	FundViewOutlined,
	AreaChartOutlined,
	FileSearchOutlined,
	UnorderedListOutlined,
	SafetyOutlined,
	ClockCircleOutlined,
	MenuFoldOutlined,
	MenuUnfoldOutlined,
	AppstoreAddOutlined,
} from '@ant-design/icons'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import { useModules } from '../../contexts/ModulesContext'
import DepartmentSelector from './DepartmentSelector'
import ApiTokensDrawer from '../admin/ApiTokensDrawer'
import { cn } from '@/utils/cn'

const { Header, Content, Sider } = Layout

interface AppLayoutProps {
	children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
	const [collapsed, setCollapsed] = useState(false)
	const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)
	const [isMobile, setIsMobile] = useState(false)
	const [apiTokensDrawerOpen, setApiTokensDrawerOpen] = useState(false)
	const location = useLocation()
	const navigate = useNavigate()
	const { user, logout } = useAuth()
	const { mode, toggleTheme } = useTheme()
	const { hasModule } = useModules()

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
	const founderMenuItem =
		(user?.role === 'FOUNDER' || user?.role === 'ADMIN') &&
		hasModule('FOUNDER_DASHBOARD')
			? [
					{
						key: '/founder/dashboard',
						icon: <TrophyOutlined />,
						label: <Link to='/founder/dashboard'>Дашборд учредителя</Link>,
					},
			]
			: []

	// Business Operation Mappings - ADMIN and MANAGER only
	const businessOperationMappingsMenuItem =
		user?.role === 'ADMIN' || user?.role === 'MANAGER'
			? [
					{
						key: '/business-operation-mappings',
						icon: <SettingOutlined />,
						label: (
							<Link to='/business-operation-mappings'>Маппинг операций</Link>
						),
					},
			]
			: []

	const taxRatesMenuItem =
		user?.role === 'ADMIN' || user?.role === 'ACCOUNTANT'
			? [
					{
						key: '/references/tax-rates',
						icon: <SafetyOutlined />,
						label: <Link to='/references/tax-rates'>Налоговые ставки</Link>,
					},
			]
			: []

	const baseMenuItems = [
		...founderMenuItem,
		{
			key: '/dashboard',
			icon: <DashboardOutlined />,
			label: <Link to='/dashboard'>Дашборд</Link>,
		},
		{
			key: 'bdr-submenu',
			icon: <LineChartOutlined />,
			label: 'БДР (Доходы и Расходы)',
			children: [
				{
					key: '/analytics/budget-income-statement',
					icon: <LineChartOutlined />,
					label: (
						<Link to='/analytics/budget-income-statement'>БДР Дашборд</Link>
					),
				},
				{
					key: '/analytics/customer-metrics',
					icon: <TeamOutlined />,
					label: (
						<Link to='/analytics/customer-metrics'>Клиентские метрики</Link>
					),
				},
				{
					key: '/analytics/revenue-extended',
					icon: <DollarCircleOutlined />,
					label: (
						<Link to='/analytics/revenue-extended'>Аналитика доходов</Link>
					),
				},
				{
					key: '/analytics/unified-dashboard',
					icon: <FundOutlined />,
					label: (
						<Link to='/analytics/unified-dashboard'>Финансовый дашборд</Link>
					),
				},
			],
		},
		{
			key: 'cast-submenu',
			icon: <FundOutlined />,
			label: 'Расходы',
			children: [
				{
					key: '/expenses',
					icon: <FileTextOutlined />,
					label: <Link to='/expenses'>Заявки</Link>,
				},
				{
					key: '/budget',
					icon: <DollarOutlined />,
					label: <Link to='/budget'>Бюджет</Link>,
				},
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

		...(hasModule('AI_FORECAST') || hasModule('CREDIT_PORTFOLIO')
			? [
					{
						key: 'finance-submenu',
						icon: <DollarCircleOutlined />,
						label: 'Финансы',
						children: [
							...(hasModule('AI_FORECAST')
								? [
										{
											key: 'bank-transactions-submenu',
											icon: <BankOutlined />,
											label: 'Банковские операции',
											children: [
												{
													key: '/bank-transactions',
													icon: <UnorderedListOutlined />,
													label: (
														<Link to='/bank-transactions'>
															Список транзакций
														</Link>
													),
												},
												{
													key: '/bank-transactions/analytics',
													icon: <FundViewOutlined />,
													label: (
														<Link to='/bank-transactions/analytics'>
															Аналитика
														</Link>
													),
												},
											],
										},
								]
								: []),
							...(hasModule('CREDIT_PORTFOLIO')
								? [
										{
											key: 'credit-portfolio-submenu',
											icon: <CreditCardOutlined />,
											label: 'Кредитный портфель',
											children: [
												{
													key: '/credit-portfolio',
													icon: <DashboardOutlined />,
													label: <Link to='/credit-portfolio'>Обзор</Link>,
												},
												{
													key: '/credit-portfolio/analytics',
													icon: <FundViewOutlined />,
													label: (
														<Link to='/credit-portfolio/analytics'>
															Расширенная аналитика
														</Link>
													),
												},
												{
													key: '/credit-portfolio/compare',
													icon: <LineChartOutlined />,
													label: (
														<Link to='/credit-portfolio/compare'>
															Сравнение периодов
														</Link>
													),
												},
												{
													key: '/credit-portfolio/kpi',
													icon: <TrophyOutlined />,
													label: (
														<Link to='/credit-portfolio/kpi'>KPI метрики</Link>
													),
												},
												{
													key: '/credit-portfolio/cash-flow',
													icon: <AreaChartOutlined />,
													label: (
														<Link to='/credit-portfolio/cash-flow'>
															Денежные потоки
														</Link>
													),
												},
												{
													key: '/credit-portfolio/contracts',
													icon: <FileSearchOutlined />,
													label: (
														<Link to='/credit-portfolio/contracts'>
															Договоры
														</Link>
													),
												},
											],
										},
								]
								: []),
						],
					},
			]
			: []),

		...(hasModule('REVENUE_BUDGET')
			? [
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
								key: '/revenue/planning',
								icon: <ProjectOutlined />,
								label: <Link to='/revenue/planning'>Планирование</Link>,
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
							{
								key: '/revenue/customer-metrics',
								icon: <TeamOutlined />,
								label: (
									<Link to='/revenue/customer-metrics'>Клиентские метрики</Link>
								),
							},
							{
								key: '/revenue/seasonality',
								icon: <LineChartOutlined />,
								label: (
									<Link to='/revenue/seasonality'>Коэффициенты сезонности</Link>
								),
							},
							{
								key: '/revenue/analytics',
								icon: <BarChartOutlined />,
								label: <Link to='/revenue/analytics'>Аналитика доходов</Link>,
							},
						],
					},
			]
			: []),

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
				...(hasModule('AI_FORECAST')
					? [
							{
								key: '/forecast',
								icon: <FundOutlined />,
								label: <Link to='/forecast'>Прогноз расходов</Link>,
							},
					]
					: []),
				{
					key: '/analytics',
					label: <Link to='/analytics'>Дашборд</Link>,
				},
				{
					key: '/analytics/balance',
					label: <Link to='/analytics/balance'>План-Факт-Остаток</Link>,
				},
				...(hasModule('ADVANCED_ANALYTICS')
					? [
							{
								key: '/analytics/extended',
								label: (
									<Link to='/analytics/extended'>Расширенная аналитика</Link>
								),
							},
					]
					: []),
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
				...(hasModule('PAYROLL_KPI')
					? [
							{
								key: '/payroll/kpi',
								label: <Link to='/payroll/kpi'>KPI сотрудников</Link>,
							},
					]
					: []),
				...(hasModule('PAYROLL_KPI')
					? [
							{
								key: '/kpi/analytics',
								label: <Link to='/kpi/analytics'>Аналитика КПИ</Link>,
							},
					]
					: []),
				{
					key: '/payroll/analytics',
					label: <Link to='/payroll/analytics'>Аналитика ФОТ</Link>,
				},
				{
					key: '/payroll/ndfl',
					label: <Link to='/payroll/ndfl'>Калькулятор НДФЛ</Link>,
				},
				...(user?.role === 'ADMIN' || user?.role === 'MANAGER'
					? [
							{
								key: '/payroll/scenarios',
								label: <Link to='/payroll/scenarios'>Сценарии ФОТ</Link>,
							},
					]
					: []),
			],
		},
		{
			key: 'timesheets-submenu',
			icon: <ClockCircleOutlined />,
			label: 'Отдел Кадров',
			children: [
				...(hasModule('HR_DEPARTMENT')
					? [
							{
								key: '/timesheets',
								icon: <ClockCircleOutlined />,
								label: <Link to='/timesheets'>Табель</Link>,
							},
					]
					: []),
				{
					key: '/timesheets/analytics',
					icon: <BarChartOutlined />,
					label: <Link to='/timesheets/analytics'>Аналитика табеля</Link>,
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
				...taxRatesMenuItem,
				...businessOperationMappingsMenuItem,
			],
		},
	]

	// Add admin-only menu items
	const menuItems =
		user?.role === 'ADMIN'
			? [
					...baseMenuItems,
					{
						key: '/module-settings',
						icon: <AppstoreAddOutlined />,
						label: <Link to='/module-settings'>Модули</Link>,
					},
					{
						key: '/departments',
						icon: <BankOutlined />,
						label: <Link to='/departments'>Отделы</Link>,
					},
					{
						key: '/users',
						icon: <UserOutlined />,
						label: <Link to='/users'>Пользователи</Link>,
					},
					{
						key: 'api-tokens',
						icon: <KeyOutlined />,
						label: 'API Токены',
						onClick: () => setApiTokensDrawerOpen(true),
					},
			]
			: baseMenuItems

	// Menu content component (reused for both Sider and Drawer)
	const menuContent = (
		<>
			<div
				className={cn(
					"h-16 flex items-center justify-center transition-all duration-300",
					collapsed && !isMobile ? "px-2" : "px-4"
				)}
			>
				<div className={cn(
					"text-white font-bold tracking-wider transition-all duration-300",
					collapsed && !isMobile ? "text-xl" : "text-2xl"
				)}>
					{collapsed && !isMobile ? 'ITB' : 'BDR'}
				</div>
			</div>
			<Menu
				theme='dark'
				selectedKeys={[location.pathname]}
				mode='inline'
				items={menuItems}
				defaultSelectedKeys={[location.pathname]}
				className="bg-transparent border-none"
				style={{ background: 'transparent' }}
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
					onCollapse={value => setCollapsed(value)}
					breakpoint='md'
					collapsedWidth={80}
					width={260}
					className="!bg-[#020617] !border-r !border-white/5 shadow-xl z-20"
					trigger={null}
				>
					{menuContent}
				</Sider>
			)}

			{/* Mobile Drawer */}
			{isMobile && (
				<Drawer
					placement='left'
					onClose={() => setMobileDrawerOpen(false)}
					open={mobileDrawerOpen}
					styles={{ body: { padding: 0, background: '#001529' } }}
					width={280}
				>
					{menuContent}
				</Drawer>
			)}

			<Layout className="bg-[#f8fafc] dark:bg-[#0f172a] transition-colors duration-300">
				<Header
					className={cn(
						"sticky top-0 z-10 w-full flex items-center justify-between px-6 h-16",
						"bg-white/80 dark:bg-[#0f172a]/80 backdrop-blur-md border-b border-gray-200/50 dark:border-white/5",
						"transition-all duration-300 shadow-sm"
					)}
					style={{ padding: 0 }}
				>
					<div className="flex items-center px-4">
						{isMobile ? (
							<Button
								type='text'
								icon={<MenuOutlined />}
								onClick={() => setMobileDrawerOpen(true)}
								className="text-lg mr-2"
							/>
						) : (
							<Button
								type="text"
								icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
								onClick={() => setCollapsed(!collapsed)}
								className="text-lg mr-4 hover:bg-gray-100 dark:hover:bg-gray-800"
							/>
						)}
						<div className="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-gray-800 to-gray-600 dark:from-gray-100 dark:to-gray-300">
							{isMobile ? 'BDR' : 'Budget Manager'}
						</div>
					</div>

					<div className="flex items-center gap-2 px-4">
						<DepartmentSelector />
						
						<Tooltip title={mode === 'dark' ? 'Светлая тема' : 'Темная тема'}>
							<Button
								type='text'
								icon={
									mode === 'dark' ? (
										<BulbFilled className="text-yellow-400 text-lg" />
									) : (
										<BulbOutlined className="text-gray-600 text-lg" />
									)
								}
								onClick={toggleTheme}
								className="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
							/>
						</Tooltip>

						<Dropdown menu={{ items: userMenuItems }} placement='bottomRight' trigger={['click']}>
							<Button
								type='text'
								className="h-10 px-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
							>
								<Space>
									<Avatar 
										size='small' 
										icon={<UserOutlined />} 
										className="bg-primary/10 text-primary"
									/>
									{!isMobile && (
										<span className="font-medium text-sm">{user?.full_name || user?.username}</span>
									)}
								</Space>
							</Button>
						</Dropdown>
					</div>
				</Header>
				
				<Content className="p-4 md:p-6 overflow-auto">
					<div className="max-w-[1600px] mx-auto w-full animate-fade-in">
						{children}
					</div>
				</Content>
			</Layout>

			{/* API Tokens Drawer */}
			<ApiTokensDrawer
				visible={apiTokensDrawerOpen}
				onClose={() => setApiTokensDrawerOpen(false)}
			/>
		</Layout>
	)
}

export default AppLayout
