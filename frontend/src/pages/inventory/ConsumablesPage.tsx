import React from 'react'
import { ShoppingCart } from 'lucide-react'

export default function ConsumablesPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <ShoppingCart className="w-16 h-16 text-gray-300 dark:text-gray-600" />
      <h1 className="text-2xl font-bold text-gray-700 dark:text-gray-300">מוצרים מתכלים</h1>
      <p className="text-gray-500 dark:text-gray-400">דף זה בפיתוח</p>
    </div>
  )
}
