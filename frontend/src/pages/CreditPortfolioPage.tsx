import Filters from '@/legacy/components/Filters'
import CreditDashboard from '@/legacy/pages/CreditDashboard'
import { useDepartment } from '@/contexts/DepartmentContext'

export default function CreditPortfolioPage() {
	const { selectedDepartment } = useDepartment()

	return (
		<div className='space-y-6 p-4 md:p-6'>
			<div className='bg-white rounded-2xl shadow-sm border border-gray-100'>
				<Filters />
			</div>

			<CreditDashboard departmentId={selectedDepartment?.id} />
		</div>
	)
}
