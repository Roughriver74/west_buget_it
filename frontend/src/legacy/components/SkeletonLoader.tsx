import { motion } from 'framer-motion'
import { Skeleton } from '@/legacy/components/ui/skeleton'

export const SkeletonCard = () => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
    <Skeleton className="h-[120px] w-full rounded-xl" />
  </motion.div>
)

export const SkeletonChart = () => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
    <Skeleton className="h-[400px] w-full rounded-xl" />
  </motion.div>
)

interface SkeletonTextProps {
  lines?: number
}

export const SkeletonText = ({ lines = 3 }: SkeletonTextProps) => (
  <div className="p-5 space-y-3">
    {Array.from({ length: lines }).map((_, i) => (
      <motion.div
        key={i}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: i * 0.1 }}
      >
        <Skeleton className="h-4 rounded" style={{ width: `${100 - i * 10}%` }} />
      </motion.div>
    ))}
  </div>
)

export const SkeletonDashboard = () => (
  <div className="p-5">
    <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-5 mb-8">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {Array.from({ length: 2 }).map((_, i) => (
        <SkeletonChart key={i} />
      ))}
    </div>
  </div>
)

export default {
  Card: SkeletonCard,
  Chart: SkeletonChart,
  Text: SkeletonText,
  Dashboard: SkeletonDashboard,
}

