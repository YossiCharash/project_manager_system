import React from 'react'
import { ShieldOff, Lock } from 'lucide-react'

export function AccessDenied() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 text-center">
      <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
        <ShieldOff className="w-8 h-8 text-red-500 dark:text-red-400" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">גישה נדחתה</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          אין לך הרשאה לצפות בדף זה.
        </p>
      </div>
    </div>
  )
}

export function NoPermissions() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 text-center">
      <div className="w-16 h-16 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
        <Lock className="w-8 h-8 text-yellow-500 dark:text-yellow-400" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">אין הרשאות</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          לא הוקצו לך הרשאות גישה. אנא פנה למנהל המערכת.
        </p>
      </div>
    </div>
  )
}
