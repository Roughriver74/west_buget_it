import React, { useState, useMemo } from 'react'
import { Typography, Card, Select, Space, Button, message, theme } from 'antd'
import {
	DownloadOutlined,
	UploadOutlined,
	FileExcelOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useTheme } from '@/contexts/ThemeContext'
import { timesheetsApi } from '@/api'
import { MONTHS_RU } from '@/types/timesheet'
import TimesheetGrid from '@/components/timesheet/TimesheetGrid'
import type { TimesheetGrid as TimesheetGridData } from '@/types/timesheet'

const { Title, Paragraph } = Typography
const { Option } = Select

const TimesheetsGridPage: React.FC = () => {
	const { selectedDepartment } = useDepartment()
	const { mode } = useTheme()
	const { token } = theme.useToken()
	const isDark = mode === 'dark'

	const currentDate = new Date()
	const currentYear = currentDate.getFullYear()
	const currentMonth = currentDate.getMonth() + 1 // 1-12

	const [selectedYear, setSelectedYear] = useState(currentYear)
	const [selectedMonth, setSelectedMonth] = useState(currentMonth)

	// Generate years list (current year +/- 2 years)
	const years = useMemo(
		() => Array.from({ length: 5 }, (_, i) => currentYear - 2 + i),
		[currentYear]
	)

	// Fetch timesheet grid data
	const { data: gridData, isLoading } = useQuery<TimesheetGridData>({
		queryKey: [
			'timesheets-grid',
			selectedYear,
			selectedMonth,
			selectedDepartment?.id,
		],
		queryFn: () =>
			timesheetsApi.getTimesheetGrid({
				year: selectedYear,
				month: selectedMonth,
				department_id: selectedDepartment?.id,
			}),
		enabled: !!selectedDepartment?.id,
	})

	// Export to Excel
	const handleExport = async () => {
		try {
			const blob = await timesheetsApi.exportTimesheetsToExcel({
				year: selectedYear,
				month: selectedMonth,
				department_id: selectedDepartment?.id,
			})

			// Create download link
			const url = window.URL.createObjectURL(blob)
			const link = document.createElement('a')
			link.href = url
			link.download = `timesheet_${selectedYear}_${selectedMonth}.xlsx`
			document.body.appendChild(link)
			link.click()
			document.body.removeChild(link)
			window.URL.revokeObjectURL(url)

			message.success('Табель экспортирован в Excel')
		} catch (error) {
			message.error('Ошибка при экспорте табеля')
			console.error('Export error:', error)
		}
	}

	// Download template
	const handleDownloadTemplate = async () => {
		try {
			const blob = await timesheetsApi.downloadTemplate('ru')

			const url = window.URL.createObjectURL(blob)
			const link = document.createElement('a')
			link.href = url
			link.download = `timesheet_template.xlsx`
			document.body.appendChild(link)
			link.click()
			document.body.removeChild(link)
			window.URL.revokeObjectURL(url)

			message.success('Шаблон загружен')
		} catch (error) {
			message.error('Ошибка при загрузке шаблона')
			console.error('Download template error:', error)
		}
	}

	return (
		<div>
			<div
				style={{
					marginBottom: 24,
					display: 'flex',
					justifyContent: 'space-between',
					alignItems: 'flex-start',
				}}
			>
				<div>
					<Title level={2}>Табель учета рабочего времени</Title>
					<Paragraph>
						Учет отработанного времени сотрудников по дням месяца
					</Paragraph>
				</div>

				<Space direction='vertical' align='end' size='middle'>
					<Space align='center'>
						<span style={{ fontSize: 16, fontWeight: 500 }}>Период:</span>
						<Select
							value={selectedMonth}
							onChange={setSelectedMonth}
							style={{ width: 150 }}
							size='large'
						>
							{MONTHS_RU.map(month => (
								<Option key={month.value} value={month.value}>
									{month.label}
								</Option>
							))}
						</Select>
						<Select
							value={selectedYear}
							onChange={setSelectedYear}
							style={{ width: 120 }}
							size='large'
						>
							{years.map(year => (
								<Option key={year} value={year}>
									{year}
								</Option>
							))}
						</Select>
					</Space>

					<Space>
						<Button
							icon={<FileExcelOutlined />}
							onClick={handleDownloadTemplate}
						>
							Скачать шаблон
						</Button>
						<Button
							icon={<UploadOutlined />}
							disabled
							title='Импорт из Excel (в разработке)'
						>
							Импорт
						</Button>
						<Button
							type='primary'
							icon={<DownloadOutlined />}
							onClick={handleExport}
							loading={isLoading}
						>
							Экспорт в Excel
						</Button>
					</Space>
				</Space>
			</div>

			<Card
				style={{
					backgroundColor: isDark ? token.colorBgElevated : undefined,
					border: isDark ? `1px solid ${token.colorBorder}` : undefined,
					boxShadow: isDark ? '0 6px 20px rgba(0,0,0,0.45)' : undefined,
				}}
				bodyStyle={{ padding: 24, backgroundColor: 'transparent' }}
			>
				{gridData ? (
					<TimesheetGrid data={gridData} loading={isLoading} />
				) : (
					<div
						style={{
							padding: 40,
							textAlign: 'center',
							color: isDark ? token.colorTextSecondary : '#999',
						}}
					>
						<Paragraph>Выберите отдел для просмотра табеля</Paragraph>
					</div>
				)}
			</Card>

			<div
				style={{
					marginTop: 16,
					padding: 16,
					borderRadius: 8,
					backgroundColor: isDark ? 'rgba(64, 169, 255, 0.12)' : '#f0f5ff',
					border: isDark
						? `1px solid ${token.colorBorder}`
						: '1px solid #d6e4ff',
					color: isDark ? token.colorText : undefined,
				}}
			>
				<Title level={5}>Инструкция:</Title>
				<ul style={{ marginBottom: 0 }}>
					<li>Выберите месяц и год для просмотра табеля</li>
					<li>Кликните по ячейке для редактирования количества часов</li>
					<li>Табель автоматически сохраняется после редактирования</li>
					<li>Используйте "Экспорт в Excel" для выгрузки данных</li>
					<li>Импорт из Excel позволяет массово обновить табель</li>
					<li>Утверждение табеля доступно руководителям и HR</li>
				</ul>
			</div>
		</div>
	)
}

export default TimesheetsGridPage
