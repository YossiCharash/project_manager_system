import React from 'react'
import { BookOpen } from 'lucide-react'

export default function UserGuide() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center gap-4 bg-gray-50 dark:bg-gray-900">
      <BookOpen className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">מדריך למשתמש</h1>
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
