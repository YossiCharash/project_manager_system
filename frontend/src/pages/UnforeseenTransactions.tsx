import React from 'react'
import { useParams } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'

export default function UnforeseenTransactions() {
  const { projectId } = useParams<{ projectId: string }>()
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <AlertCircle className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">עסקאות בלתי צפויות</h1>
      {projectId && <p className="text-sm text-gray-400">פרויקט #{projectId}</p>}
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
