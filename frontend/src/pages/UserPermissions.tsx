import React from 'react'
import { useParams } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export default function UserPermissions() {
  const { userId } = useParams<{ userId: string }>()
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <ShieldCheck className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">הרשאות משתמש #{userId}</h1>
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
