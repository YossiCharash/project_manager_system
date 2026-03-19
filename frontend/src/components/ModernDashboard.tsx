import React from 'react'
import { DashboardAPI } from '../lib/apiClient'
import type { ProjectWithFinance, DashboardSnapshot } from '../types/api'
import { useNavigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'

interface ModernDashboardProps {
  onProjectClick?: (project: ProjectWithFinance) => void
  onProjectEdit?: (project: ProjectWithFinance) => void
}

const ModernDashboard: React.FC<ModernDashboardProps> = ({ onProjectClick, onProjectEdit }) => {
  const navigate = useNavigate()
  const [data, setData] = React.useState<DashboardSnapshot | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const load = React.useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const snapshot = await DashboardAPI.getDashboardSnapshot()
      setData(snapshot)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'שגיאה בטעינת הנתונים')
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => { load() }, [load])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400">
        טוען נתונים...
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={load}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
        >
          נסה שוב
        </button>
      </div>
    )
  }

  if (!data) return null

  const projects = data.projects ?? []
  const summary = data.summary ?? { total_income: 0, total_expense: 0, total_profit: 0 }

  return (
    <div className="space-y-6" dir="rtl">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">סה"כ הכנסות</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {summary.total_income.toLocaleString('he-IL')} ₪
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">סה"כ הוצאות</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {summary.total_expense.toLocaleString('he-IL')} ₪
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">רווח נקי</p>
          <p className={`text-2xl font-bold mt-1 ${summary.total_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {summary.total_profit.toLocaleString('he-IL')} ₪
          </p>
        </div>
      </div>

      {/* Projects list */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white">פרויקטים</h2>
          <button
            onClick={load}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="רענן"
          >
            <RefreshCw className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            אין פרויקטים פעילים
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {projects.map(project => (
              <div
                key={project.id}
                className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                onClick={() => {
                  if (onProjectClick) {
                    onProjectClick(project)
                  } else {
                    navigate(`/projects/${project.id}`)
                  }
                }}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    project.status_color === 'green' ? 'bg-green-500' :
                    project.status_color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{project.name}</p>
                    {project.city && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">{project.city}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      הכנסה: {(project.income_month_to_date ?? 0).toLocaleString('he-IL')} ₪
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      הוצאה: {(project.expense_month_to_date ?? 0).toLocaleString('he-IL')} ₪
                    </p>
                  </div>
                  {onProjectEdit && (
                    <button
                      onClick={e => { e.stopPropagation(); onProjectEdit(project) }}
                      className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      ערוך
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModernDashboard
