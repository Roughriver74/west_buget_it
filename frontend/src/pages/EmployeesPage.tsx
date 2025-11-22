import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
	Button,
	Space,
	Card,
	Tag,
	Input,
	Select,
	message,
	Popconfirm,
	Statistic,
	Row,
	Col,
	Modal} from 'antd'
import {
	PlusOutlined,
	EditOutlined,
	DeleteOutlined,
	SearchOutlined,
	UserOutlined,
	DownloadOutlined,
	UploadOutlined} from '@ant-design/icons'
import { useDepartment } from '../contexts/DepartmentContext'
import { useTheme } from '../contexts/ThemeContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import {
	employeeAPI,
	Employee,
	payrollPlanAPI,
	PayrollPlanWithEmployee,
	payrollActualAPI,
	PayrollActualWithEmployee} from '../api/payroll'
import { formatCurrency } from '../utils/formatters'
import EmployeeFormModal from '../components/employees/EmployeeFormModal'
import EmployeeImportModal from '../components/employees/EmployeeImportModal'

const { Search } = Input
const { Option } = Select

const STATUS_COLORS: Record<string, string> = {
	ACTIVE: 'green',
	ON_VACATION: 'blue',
	ON_LEAVE: 'orange',
	FIRED: 'red'}

const STATUS_LABELS: Record<string, string> = {
	ACTIVE: 'Активен',
	ON_VACATION: 'В отпуске',
	ON_LEAVE: 'В отпуске/Больничный',
	FIRED: 'Уволен'}

export default function EmployeesPage() {
	const navigate = useNavigate()
	const queryClient = useQueryClient()
	const { selectedDepartment } = useDepartment()
	const { mode } = useTheme()
	const [searchText, setSearchText] = useState('')
	const [statusFilter, setStatusFilter] = useState<string | undefined>()
	const [modalVisible, setModalVisible] = useState(false)
	const [selectedEmployee, setSelectedEmployee] = useState<
		Employee | undefined
	>()
	const [importModalVisible, setImportModalVisible] = useState(false)

	// Fetch employees
	const { data: employees = [], isLoading } = useQuery<Employee[]>({
		queryKey: ['employees', selectedDepartment?.id, searchText, statusFilter],
		queryFn: () =>
			employeeAPI.list({
				department_id: selectedDepartment?.id,
				search: searchText || undefined,
				status: statusFilter})})

	// Fetch payroll plans for current year
	const currentYear = new Date().getFullYear()
	const { data: payrollPlans = [] } = useQuery<PayrollPlanWithEmployee[]>({
		queryKey: ['payroll-plans', selectedDepartment?.id, currentYear],
		queryFn: async () => {
			// Получаем все планы за год через несколько запросов, так как лимит API = 1000
			let allPlans: PayrollPlanWithEmployee[] = []
			let skip = 0
			const limit = 1000 // Максимальный лимит API
			let hasMore = true

			while (hasMore) {
				const plans = await payrollPlanAPI.list({
					department_id: selectedDepartment?.id,
					year: currentYear,
					skip,
					limit})
				allPlans = [...allPlans, ...plans]
				hasMore = plans.length === limit
				skip += limit
			}

			return allPlans
		},
		enabled: !!selectedDepartment?.id})

	// Fetch payroll actuals (фактические выплаты) for current year
	const { data: payrollActuals = [] } = useQuery<PayrollActualWithEmployee[]>({
		queryKey: ['payroll-actuals', selectedDepartment?.id, currentYear],
		queryFn: async () => {
			// Получаем все выплаты за год через несколько запросов, так как лимит API = 1000
			let allActuals: PayrollActualWithEmployee[] = []
			let skip = 0
			const limit = 1000 // Максимальный лимит API
			let hasMore = true

			while (hasMore) {
				const actuals = await payrollActualAPI.list({
					department_id: selectedDepartment?.id,
					year: currentYear,
					skip,
					limit})
				allActuals = [...allActuals, ...actuals]
				hasMore = actuals.length === limit
				skip += limit
			}

			return allActuals
		},
		enabled: !!selectedDepartment?.id})

	// Delete employee mutation
	const deleteMutation = useMutation({
		mutationFn: employeeAPI.delete,
		onSuccess: () => {
			message.success('Сотрудник удален')
			queryClient.invalidateQueries({ queryKey: ['employees'] })
		},
		onError: (error: any) => {
			const errorDetail = error.response?.data?.detail

			// Check if it's a structured error with related records
			if (
				errorDetail &&
				typeof errorDetail === 'object' &&
				errorDetail.message
			) {
				Modal.error({
					title: errorDetail.message || 'Невозможно удалить сотрудника',
					content: (
						<div>
							<p>
								<strong>Причина:</strong>{' '}
								{errorDetail.reason || 'Неизвестная причина'}
							</p>
							{errorDetail.related_records &&
								errorDetail.related_records.length > 0 && (
									<>
										<p>
											<strong>Связанные записи:</strong>
										</p>
										<ul>
											{errorDetail.related_records.map(
												(record: string, index: number) => (
													<li key={index}>{record}</li>
												)
											)}
										</ul>
									</>
								)}
							{errorDetail.suggestion && (
								<p
									style={{
										marginTop: 16,
										fontWeight: 'bold',
										color: mode === 'dark' ? '#69b7ff' : '#1890ff'}}
								>
									💡 {errorDetail.suggestion}
								</p>
							)}
						</div>
					),
					width: 600})
			} else {
				// Fallback for other errors
				message.error(
					typeof errorDetail === 'string'
						? errorDetail
						: 'Ошибка при удалении сотрудника'
				)
			}
		}})

	const handleDelete = (id: number) => {
		deleteMutation.mutate(id)
	}

	const handleCreate = () => {
		setSelectedEmployee(undefined)
		setModalVisible(true)
	}

	const handleEdit = (employee: Employee) => {
		setSelectedEmployee(employee)
		setModalVisible(true)
	}

	const handleCloseModal = () => {
		setModalVisible(false)
		setSelectedEmployee(undefined)
	}

	const handleExport = async () => {
		try {
			await employeeAPI.exportToExcel({
				department_id: selectedDepartment?.id,
				status: statusFilter})
			message.success('Экспорт выполнен успешно')
		} catch (error) {
			message.error('Ошибка при экспорте')
		}
	}

	const handleImport = () => {
		setImportModalVisible(true)
	}

	const handleCloseImportModal = () => {
		setImportModalVisible(false)
		queryClient.invalidateQueries({ queryKey: ['employees'] })
	}

	// Calculate statistics
	const activeEmployees = employees.filter(e => e.status === 'ACTIVE')

	// Фильтруем планы по департаменту и году (ВАЖНО: делаем это один раз)
	const filteredPlans = payrollPlans.filter(
		plan =>
			(!selectedDepartment?.id ||
				plan.department_id === selectedDepartment.id) &&
			plan.year === currentYear
	)

	// Если есть планы за текущий год и выбранный департамент, используем их
	const hasPlans = filteredPlans.length > 0

	let totalPayroll = 0
	let totalSalary = 0
	let totalBonuses = 0

	if (hasPlans) {
		// Используем данные из планов за текущий год
		// total_planned уже содержит все суммы (оклад + премии) за месяц
		// Суммируем все total_planned за год - это годовая сумма с премиями
		// Это должно совпадать с суммой на странице планов
		totalPayroll = filteredPlans.reduce(
			(sum, plan) => sum + Number(plan.total_planned || 0),
			0
		)
		// В планах base_salary - это месячный оклад для каждого месяца
		// Суммируем все месячные оклады - получаем годовую сумму окладов
		const totalMonthlySalary = filteredPlans.reduce(
			(sum, plan) => sum + Number(plan.base_salary || 0),
			0
		)
		totalSalary = totalMonthlySalary // Годовая сумма окладов
		totalBonuses = totalPayroll - totalSalary // Премии = общая сумма из планов - оклады
	} else {
		// Fallback: рассчитываем на основе данных сотрудников
		totalSalary = activeEmployees.reduce(
			(sum, e) => sum + Number(e.base_salary),
			0
		)
		totalBonuses = activeEmployees.reduce(
			(sum, e) =>
				sum +
				Number(e.monthly_bonus_base || 0) * 12 +
				Number(e.quarterly_bonus_base || 0) * 4 +
				Number(e.annual_bonus_base || 0),
			0
		)
		totalPayroll = totalSalary * 12 + totalBonuses
	}

	// Рассчитываем сумму фактических выплат за текущий год
	// Используем ТОЧНО ту же логику, что и на странице планирования
	// Фильтруем выплаты по департаменту и году
	const filteredActuals = payrollActuals.filter(
		actual =>
			(!selectedDepartment?.id ||
				actual.department_id === selectedDepartment.id) &&
			actual.year === currentYear
	)

	// Группируем по месяцам ТОЧНО так же, как на странице планирования
	// На странице планирования: MONTHS.map((monthName, index) => { const month = index + 1; ... })
	const MONTHS_ARRAY = Array.from({ length: 12 }, (_, i) => i + 1) // [1, 2, 3, ..., 12]
	const monthlyPaidData = MONTHS_ARRAY.map(month => {
		// Фильтруем выплаты за конкретный месяц - ТОЧНО как на странице планирования
		const monthActuals = filteredActuals.filter(a => a.month === month)
		// Суммируем total_paid - ТОЧНО как на странице планирования
		const totalPaid = monthActuals.reduce(
			(sum, a) => sum + Number(a.total_paid || 0),
			0
		)
		return totalPaid
	})
	// Суммируем все месяцы - ТОЧНО как на странице планирования: yearTotalPaid = monthlyData.reduce((sum, m) => sum + m.totalPaid, 0)
	const totalPaid = monthlyPaidData.reduce((sum, paid) => sum + paid, 0)

	// Helper function to calculate progressive NDFL for annual income
	const calculateProgressiveNDFL = (
		annualIncome: number,
		year: number = 2025
	): number => {
		// Tax brackets for 2025+ (5-tier progressive system)
		const brackets2025 = [
			{ limit: 2400000, rate: 0.13 },
			{ limit: 5000000, rate: 0.15 },
			{ limit: 20000000, rate: 0.18 },
			{ limit: 50000000, rate: 0.2 },
			{ limit: Infinity, rate: 0.22 },
		]

		// Tax brackets for 2024 (2-tier system)
		const brackets2024 = [
			{ limit: 5000000, rate: 0.13 },
			{ limit: Infinity, rate: 0.15 },
		]

		const brackets = year >= 2025 ? brackets2025 : brackets2024
		let totalTax = 0
		let remainingIncome = annualIncome
		let previousLimit = 0

		for (const bracket of brackets) {
			const taxableInBracket = Math.min(
				remainingIncome,
				bracket.limit - previousLimit
			)
			if (taxableInBracket <= 0) break

			totalTax += taxableInBracket * bracket.rate
			remainingIncome -= taxableInBracket
			previousLimit = bracket.limit

			if (remainingIncome <= 0) break
		}

		return Math.round(totalTax)
	}

	// Tax calculations (расчет налогов по прогрессивной шкале)
	const socialTaxRate = 0.302 // 30.2% страховые взносы (ПФР 22% + ОМС 5.1% + ФСС 2.9% + травматизм 0.2%)

	// Calculate NDFL
	// Если есть планы за текущий год, используем суммы из планов, иначе рассчитываем по сотрудникам
	let totalIncomeTax = 0

	if (hasPlans) {
		// Рассчитываем НДФЛ на основе сумм из планов
		// Группируем планы по сотрудникам и суммируем total_planned за год
		// Используем уже отфильтрованные планы
		const plansByEmployee = new Map<number, number>()
		filteredPlans.forEach(plan => {
			const current = plansByEmployee.get(plan.employee_id) || 0
			plansByEmployee.set(
				plan.employee_id,
				current + Number(plan.total_planned || 0)
			)
		})

		// Рассчитываем НДФЛ для каждого сотрудника на основе годовой суммы из планов
		plansByEmployee.forEach(annualIncome => {
			totalIncomeTax += calculateProgressiveNDFL(annualIncome, currentYear)
		})
	} else {
		// Fallback: рассчитываем НДФЛ на основе данных сотрудников
		totalIncomeTax = activeEmployees.reduce((sum, employee) => {
			const employeeAnnualIncome =
				Number(employee.base_salary) * 12 +
				Number(employee.monthly_bonus_base || 0) * 12 +
				Number(employee.quarterly_bonus_base || 0) * 4 +
				Number(employee.annual_bonus_base || 0)
			const employeeNDFL = calculateProgressiveNDFL(
				employeeAnnualIncome,
				currentYear
			)
			return sum + employeeNDFL
		}, 0)
	}

	const totalGross = totalPayroll // Общая начисленная сумма (gross) - годовая ЗП с премиями
	const totalSocialTax = Math.round(totalGross * socialTaxRate) // Страховые взносы
	const totalEmployerCost = totalGross + totalSocialTax // Полная стоимость для работодателя

	// Рассчитываем средний оклад из активных сотрудников
	const avgSalary =
		activeEmployees.length > 0
			? activeEmployees.reduce(
					(sum, e) => sum + Number(e.base_salary || 0),
					0
				) / activeEmployees.length
			: 0

	// Calculate effective tax rate for display
	const effectiveNDFLRate =
		totalGross > 0 ? (totalIncomeTax / totalGross) * 100 : 13

	const columns = [
		{
			title: 'ФИО',
			dataIndex: 'full_name',
			key: 'full_name',
			sorter: (a: Employee, b: Employee) =>
				a.full_name.localeCompare(b.full_name),
			render: (name: string, record: Employee) => (
				<Button
					type='link'
					onClick={() => navigate(`/employees/${record.id}`)}
					style={{ padding: 0 }}
				>
					{name}
				</Button>
			)},
		{
			title: 'Должность',
			dataIndex: 'position',
			key: 'position'},
		{
			title: 'Табельный номер',
			dataIndex: 'employee_number',
			key: 'employee_number'},
		{
			title: 'Оклад',
			dataIndex: 'base_salary',
			key: 'base_salary',
			render: (salary: number) => formatCurrency(salary),
			sorter: (a: Employee, b: Employee) =>
				Number(a.base_salary) - Number(b.base_salary)},
		{
			title: 'Премии (мес/квар/год)',
			key: 'bonuses',
			render: (_: any, record: Employee) => {
				const monthly = Number(record.monthly_bonus_base || 0)
				const quarterly = Number(record.quarterly_bonus_base || 0)
				const annual = Number(record.annual_bonus_base || 0)
				const total = monthly + quarterly + annual
				return total > 0
					? `${formatCurrency(monthly)} / ${formatCurrency(
							quarterly
						)} / ${formatCurrency(annual)}`
					: '-'
			}},
		{
			title: 'Статус',
			dataIndex: 'status',
			key: 'status',
			render: (status: string) => (
				<Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>
			),
			filters: Object.keys(STATUS_LABELS).map(key => ({
				text: STATUS_LABELS[key],
				value: key})),
			onFilter: (value: any, record: Employee) => record.status === value},
		{
			title: 'Email',
			dataIndex: 'email',
			key: 'email'},
		{
			title: 'Телефон',
			dataIndex: 'phone',
			key: 'phone'},
		{
			title: 'Дата приема',
			dataIndex: 'hire_date',
			key: 'hire_date',
			render: (date: string) =>
				date ? new Date(date).toLocaleDateString('ru-RU') : '-'},
		{
			title: 'Действия',
			key: 'actions',
			fixed: 'right' as const,
			width: 120,
			render: (_: any, record: Employee) => (
				<Space size='small'>
					<Button
						type='link'
						icon={<EditOutlined />}
						onClick={() => handleEdit(record)}
					/>
					<Popconfirm
						title='Вы уверены, что хотите удалить этого сотрудника?'
						onConfirm={() => handleDelete(record.id)}
						okText='Да'
						cancelText='Нет'
					>
						<Button type='link' danger icon={<DeleteOutlined />} />
					</Popconfirm>
				</Space>
			)},
	]

	return (
		<div style={{ padding: '24px' }}>
			<div style={{ marginBottom: '24px' }}>
				<h1
					style={{
						color:
							mode === 'dark'
								? 'rgba(255, 255, 255, 0.85)'
								: 'rgba(0, 0, 0, 0.85)'}}
				>
					<UserOutlined /> Управление сотрудниками
				</h1>
			</div>

			{/* Statistics Cards - Компактное расположение */}
			<Row gutter={[12, 12]} style={{ marginBottom: '16px' }}>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title='Всего сотрудников'
							value={employees.length}
							prefix={<UserOutlined />}
							valueStyle={{ fontSize: '20px' }}
						/>
					</Card>
				</Col>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title='Активных'
							value={activeEmployees.length}
							valueStyle={{
								color: mode === 'dark' ? '#73d13d' : '#3f8600',
								fontSize: '20px'}}
						/>
					</Card>
				</Col>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title={`ФОТ (${currentYear})`}
							value={totalPayroll}
							precision={0}
							suffix='₽'
							valueStyle={{ fontSize: '20px' }}
						/>
					</Card>
				</Col>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title='Средний оклад'
							value={avgSalary}
							precision={0}
							suffix='₽'
							valueStyle={{ fontSize: '20px' }}
						/>
					</Card>
				</Col>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title={`Выплачено (${currentYear})`}
							value={totalPaid}
							precision={0}
							suffix='₽'
							valueStyle={{
								color: mode === 'dark' ? '#73d13d' : '#3f8600',
								fontSize: '20px'}}
						/>
					</Card>
				</Col>
				<Col span={4}>
					<Card size='small'>
						<Statistic
							title={`НДФЛ (${effectiveNDFLRate.toFixed(1)}%)`}
							value={totalIncomeTax}
							precision={0}
							suffix='₽'
							valueStyle={{
								color: mode === 'dark' ? '#ff7875' : '#cf1322',
								fontSize: '20px'}}
						/>
					</Card>
				</Col>
			</Row>

			<Row gutter={[12, 12]} style={{ marginBottom: '16px' }}>
				<Col span={6}>
					<Card size='small'>
						<Statistic
							title='Страховые взносы (30.2%)'
							value={totalSocialTax}
							precision={0}
							suffix='₽'
							valueStyle={{
								color: mode === 'dark' ? '#ffa940' : '#d46b08',
								fontSize: '20px'}}
						/>
					</Card>
				</Col>
				<Col span={6}>
					<Card
						size='small'
						style={{
							backgroundColor: mode === 'dark' ? '#2b2111' : '#fff7e6',
							border:
								mode === 'dark' ? '1px solid #fa8c16' : '1px solid #ffd591'}}
					>
						<Statistic
							title={`Стоимость для компании (${currentYear})`}
							value={totalEmployerCost}
							precision={0}
							suffix='₽'
							valueStyle={{
								color: mode === 'dark' ? '#ffa940' : '#fa8c16',
								fontWeight: 'bold',
								fontSize: '20px'}}
						/>
					</Card>
				</Col>
			</Row>

			{/* Filters and Actions */}
			<Card style={{ marginBottom: '16px' }}>
				<Space
					style={{
						marginBottom: '16px',
						width: '100%',
						justifyContent: 'space-between'}}
				>
					<Space>
						<Search
							placeholder='Поиск по ФИО, должности, табельному номеру'
							allowClear
							enterButton={<SearchOutlined />}
							onSearch={setSearchText}
							style={{ width: 400 }}
						/>
						<Select
							placeholder='Статус'
							allowClear
							style={{ width: 200 }}
							onChange={setStatusFilter}
						>
							{Object.entries(STATUS_LABELS).map(([value, label]) => (
								<Option key={value} value={value}>
									{label}
								</Option>
							))}
						</Select>
					</Space>
					<Space>
						<Button icon={<UploadOutlined />} onClick={handleImport}>
							Импорт из Excel
						</Button>
						<Button icon={<DownloadOutlined />} onClick={handleExport}>
							Экспорт в Excel
						</Button>
						<Button
							type='primary'
							icon={<PlusOutlined />}
							onClick={handleCreate}
						>
							Добавить сотрудника
						</Button>
					</Space>
				</Space>

				{/* Employees Table */}
				<ResponsiveTable
					columns={columns}
					dataSource={employees}
					rowKey='id'
					loading={isLoading}
					pagination={{
						pageSize: 20,
						showSizeChanger: true,
						showTotal: total => `Всего сотрудников: ${total}`}}
					scroll={{ x: 1200 }}
					mobileLayout="card"
				/>
			</Card>

			<EmployeeFormModal
				visible={modalVisible}
				employee={selectedEmployee}
				onCancel={handleCloseModal}
			/>

			<EmployeeImportModal
				visible={importModalVisible}
				onCancel={handleCloseImportModal}
			/>
		</div>
	)
}
