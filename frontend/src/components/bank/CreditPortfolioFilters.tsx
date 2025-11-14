import { useState, useEffect, useMemo } from 'react'
import { Card, DatePicker, Select, Button, Space, Form, Row, Col } from 'antd'
import { ReloadOutlined, FilterOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
	creditPortfolioApi,
	type FinOrganization,
	type FinBankAccount,
	type FinContract,
} from '@/api/creditPortfolio'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

export interface CreditPortfolioFilterValues {
	dateFrom?: string
	dateTo?: string
	organizationIds?: number[]
	bankAccountIds?: number[]
	contractIds?: number[]
}

interface Props {
	onFilterChange: (filters: CreditPortfolioFilterValues) => void
	initialValues?: CreditPortfolioFilterValues
}

export default function CreditPortfolioFilters({
	onFilterChange,
	initialValues,
}: Props) {
	const { selectedDepartment } = useDepartment()
	const [form] = Form.useForm()

	// Local state for cascade filtering
	const [selectedOrgs, setSelectedOrgs] = useState<number[]>(
		initialValues?.organizationIds || []
	)
	const [selectedBanks, setSelectedBanks] = useState<number[]>(
		initialValues?.bankAccountIds || []
	)

	// Fetch organizations
	const { data: organizations } = useQuery({
		queryKey: ['credit-organizations', selectedDepartment?.id],
		queryFn: () =>
			creditPortfolioApi.getOrganizations({
				department_id: selectedDepartment?.id,
				is_active: true,
				limit: 100,
			}),
		enabled: !!selectedDepartment,
	})

	// Fetch bank accounts
	const { data: bankAccounts } = useQuery({
		queryKey: ['credit-bank-accounts', selectedDepartment?.id],
		queryFn: () =>
			creditPortfolioApi.getBankAccounts({
				department_id: selectedDepartment?.id,
				is_active: true,
				limit: 100,
			}),
		enabled: !!selectedDepartment,
	})

	// Fetch contracts with cascade filtering
	const contractsParams = useMemo(() => {
		const params: any = {
			department_id: selectedDepartment?.id,
			is_active: true,
			limit: 200,
		}
		// Cascade: if organizations selected, filter contracts by them
		// (This would require backend support for filtering contracts by organization)
		return params
	}, [selectedDepartment?.id, selectedOrgs, selectedBanks])

	const { data: contracts, isLoading: contractsLoading } = useQuery({
		queryKey: ['credit-contracts', contractsParams],
		queryFn: () => creditPortfolioApi.getContracts(contractsParams),
		enabled: !!selectedDepartment,
	})

	// Organization options
	const organizationOptions = useMemo(
		() =>
			(organizations || []).map((org: FinOrganization) => ({
				label: org.name,
				value: org.id,
			})),
		[organizations]
	)

	// Bank account options
	const bankAccountOptions = useMemo(
		() =>
			(bankAccounts || []).map((bank: FinBankAccount) => ({
				label: `${bank.account_number} - ${bank.bank_name || ''}`,
				value: bank.id,
			})),
		[bankAccounts]
	)

	// Contract options
	const contractOptions = useMemo(
		() =>
			(contracts || [])
				.filter((contract: FinContract) => contract.contract_number)
				.map((contract: FinContract) => ({
					label: contract.contract_number,
					value: contract.id,
				})),
		[contracts]
	)

	// Handle form submit
	const handleApply = () => {
		const values = form.getFieldsValue()

		const filters: CreditPortfolioFilterValues = {
			dateFrom: values.dateRange?.[0]?.format('YYYY-MM-DD'),
			dateTo: values.dateRange?.[1]?.format('YYYY-MM-DD'),
			organizationIds: values.organizationIds,
			bankAccountIds: values.bankAccountIds,
			contractIds: values.contractIds,
		}

		onFilterChange(filters)
	}

	// Handle reset
	const handleReset = () => {
		form.resetFields()
		setSelectedOrgs([])
		setSelectedBanks([])
		onFilterChange({})
	}

	// Update local state when org/bank selection changes
	const handleOrganizationChange = (values: number[]) => {
		setSelectedOrgs(values)
		// Clear contracts when organizations change (cascade)
		form.setFieldValue('contractIds', [])
	}

	const handleBankAccountChange = (values: number[]) => {
		setSelectedBanks(values)
		// Clear contracts when banks change (cascade)
		form.setFieldValue('contractIds', [])
	}

	// Set initial values
	useEffect(() => {
		if (initialValues) {
			const dateRange: [Dayjs, Dayjs] | undefined =
				initialValues.dateFrom && initialValues.dateTo
					? [dayjs(initialValues.dateFrom), dayjs(initialValues.dateTo)]
					: undefined

			form.setFieldsValue({
				dateRange,
				organizationIds: initialValues.organizationIds,
				bankAccountIds: initialValues.bankAccountIds,
				contractIds: initialValues.contractIds,
			})
		}
	}, [initialValues, form])

	return (
		<Card
			size='small'
			style={{ marginBottom: 16 }}
			styles={{ body: { paddingBottom: 8 } }}
		>
			<Form
				form={form}
				layout='vertical'
				onFinish={handleApply}
				style={{ marginBottom: 0 }}
			>
				<Row gutter={[16, 0]}>
					<Col xs={24} sm={12} md={6}>
						<Form.Item label='Период' name='dateRange'>
							<RangePicker
								style={{ width: '100%' }}
								format='DD.MM.YYYY'
								placeholder={['Дата с', 'Дата по']}
							/>
						</Form.Item>
					</Col>

					<Col xs={24} sm={12} md={6}>
						<Form.Item label='Организация' name='organizationIds'>
							<Select
								mode='multiple'
								placeholder='Все организации'
								options={organizationOptions}
								onChange={handleOrganizationChange}
								showSearch
								optionFilterProp='label'
								maxTagCount='responsive'
								allowClear
							/>
						</Form.Item>
					</Col>

					<Col xs={24} sm={12} md={6}>
						<Form.Item label='Банковский счет' name='bankAccountIds'>
							<Select
								mode='multiple'
								placeholder='Все счета'
								options={bankAccountOptions}
								onChange={handleBankAccountChange}
								showSearch
								optionFilterProp='label'
								maxTagCount='responsive'
								allowClear
							/>
						</Form.Item>
					</Col>

					<Col xs={24} sm={12} md={6}>
						<Form.Item
							label='Договор'
							name='contractIds'
							tooltip={
								selectedOrgs.length > 0 || selectedBanks.length > 0
									? 'Фильтруется по выбранным организациям и счетам'
									: undefined
							}
						>
							<Select
								mode='multiple'
								placeholder='Все договоры'
								options={contractOptions}
								loading={contractsLoading}
								showSearch
								optionFilterProp='label'
								maxTagCount='responsive'
								allowClear
							/>
						</Form.Item>
					</Col>
				</Row>

				<Row justify='end' style={{ marginTop: -8 }}>
					<Col>
						<Space>
							<Button icon={<ReloadOutlined />} onClick={handleReset}>
								Сбросить
							</Button>
							<Button
								type='primary'
								icon={<FilterOutlined />}
								htmlType='submit'
							>
								Применить
							</Button>
						</Space>
					</Col>
				</Row>
			</Form>
		</Card>
	)
}
