import React from 'react'
import { Package } from 'lucide-react'

export default function InventoryDashboard() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <Package className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">מלאי – לוח בקרה</h1>
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
