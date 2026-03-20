
import { useParams } from 'react-router-dom'
import { FileText } from 'lucide-react'

export default function QuoteDetail() {
  const { id } = useParams<{ id: string }>()
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">הצעת מחיר #{id}</h1>
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
