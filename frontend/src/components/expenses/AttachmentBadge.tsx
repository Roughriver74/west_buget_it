import { Badge, Tooltip } from 'antd'
import { PaperClipOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { attachmentsApi } from '@/api/attachments'

interface AttachmentBadgeProps {
  expenseId: number
}

const AttachmentBadge: React.FC<AttachmentBadgeProps> = ({ expenseId }) => {
  const { data: attachments } = useQuery({
    queryKey: ['attachments', expenseId],
    queryFn: () => attachmentsApi.getByExpenseId(expenseId),
    enabled: !!expenseId,
  })

  const count = attachments?.total || 0

  if (count === 0) {
    return null
  }

  return (
    <Tooltip title={`Вложений: ${count}`}>
      <Badge count={count} size="small" offset={[5, 0]}>
        <PaperClipOutlined style={{ color: '#1890ff' }} />
      </Badge>
    </Tooltip>
  )
}

export default AttachmentBadge
