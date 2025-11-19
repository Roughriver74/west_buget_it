import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Download, FileText, Image as ImageIcon } from 'lucide-react'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { toast } from 'sonner'
import { Button } from '@/legacy/components/ui/button'
import { cn } from '@/legacy/lib/utils'

interface ExportButtonProps {
  targetId: string
  fileName?: string
  data?: Record<string, any>[]
}

export default function ExportButton({ targetId, fileName = 'export', data }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [exporting, setExporting] = useState(false)

  const exportToImage = async () => {
    try {
      setExporting(true)
      toast.loading('Экспорт изображения...')

      const element = document.getElementById(targetId)
      if (!element) {
        toast.error('Элемент не найден')
        return
      }

      const canvas = await html2canvas(element, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false,
      })

      const link = document.createElement('a')
      link.download = `${fileName}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()

      toast.dismiss()
      toast.success('Изображение сохранено!')
      setIsOpen(false)
    } catch (error) {
      console.error('Export error:', error)
      toast.dismiss()
      toast.error('Ошибка при экспорте')
    } finally {
      setExporting(false)
    }
  }

  const exportToPDF = async () => {
    try {
      setExporting(true)
      toast.loading('Экспорт в PDF...')

      const element = document.getElementById(targetId)
      if (!element) {
        toast.error('Элемент не найден')
        return
      }

      const canvas = await html2canvas(element, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false,
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
        unit: 'px',
        format: [canvas.width, canvas.height],
      })

      pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height)
      pdf.save(`${fileName}.pdf`)

      toast.dismiss()
      toast.success('PDF сохранен!')
      setIsOpen(false)
    } catch (error) {
      console.error('Export error:', error)
      toast.dismiss()
      toast.error('Ошибка при экспорте')
    } finally {
      setExporting(false)
    }
  }

  const exportToCSV = () => {
    try {
      setExporting(true)
      toast.loading('Экспорт в CSV...')

      if (!data || !Array.isArray(data) || data.length === 0) {
        toast.error('Нет данных для экспорта')
        return
      }

      const headers = Object.keys(data[0])
      const csvContent = [
        headers.join(','),
        ...data.map(row =>
          headers
            .map(header => {
              const value = row[header]
              return typeof value === 'string' && value.includes(',') ? `"${value}"` : value
            })
            .join(',')
        ),
      ].join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${fileName}.csv`
      link.click()

      toast.dismiss()
      toast.success('CSV сохранен!')
      setIsOpen(false)
    } catch (error) {
      console.error('Export error:', error)
      toast.dismiss()
      toast.error('Ошибка при экспорте')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="relative">
      <Button onClick={() => setIsOpen(!isOpen)} disabled={exporting} className="flex items-center gap-2">
        <Download size={18} />
        <span>Экспорт</span>
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full right-0 mt-2 bg-card border border-border rounded-lg shadow-lg z-[1000] min-w-[200px] p-2"
          >
            <motion.button
              whileHover={{ backgroundColor: 'var(--muted)' }}
              onClick={exportToImage}
              disabled={exporting}
              className={cn(
                'flex items-center gap-3 w-full px-3 py-2.5 bg-transparent border-none rounded-md cursor-pointer text-sm text-foreground text-left transition-colors',
                exporting && 'opacity-50 cursor-not-allowed'
              )}
            >
              <ImageIcon size={16} />
              <span>Сохранить как PNG</span>
            </motion.button>

            <motion.button
              whileHover={{ backgroundColor: 'var(--muted)' }}
              onClick={exportToPDF}
              disabled={exporting}
              className={cn(
                'flex items-center gap-3 w-full px-3 py-2.5 bg-transparent border-none rounded-md cursor-pointer text-sm text-foreground text-left transition-colors',
                exporting && 'opacity-50 cursor-not-allowed'
              )}
            >
              <FileText size={16} />
              <span>Сохранить как PDF</span>
            </motion.button>

            {data && (
              <motion.button
                whileHover={{ backgroundColor: 'var(--muted)' }}
                onClick={exportToCSV}
                disabled={exporting}
                className={cn(
                  'flex items-center gap-3 w-full px-3 py-2.5 bg-transparent border-none rounded-md cursor-pointer text-sm text-foreground text-left transition-colors',
                  exporting && 'opacity-50 cursor-not-allowed'
                )}
              >
                <FileText size={16} />
                <span>Экспорт в CSV</span>
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

