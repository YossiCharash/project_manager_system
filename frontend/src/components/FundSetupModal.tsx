import React, { useState } from 'react'
import api from '../lib/api'

interface FundSetupModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  projectId: number
  projectStartDate?: string | null
  monthlyFundAmount?: number | null
}

const FundSetupModal: React.FC<FundSetupModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  projectId,
  projectStartDate,
  monthlyFundAmount,
}) => {
  const [amount, setAmount] = useState<number>(monthlyFundAmount ?? 0)
  const [startDate, setStartDate] = useState<string>(projectStartDate ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  React.useEffect(() => {
    if (isOpen) {
      setAmount(monthlyFundAmount ?? 0)
      setStartDate(projectStartDate ?? '')
      setError(null)
    }
  }, [isOpen, monthlyFundAmount, projectStartDate])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await api.post(`/projects/${projectId}/fund`, {
        monthly_amount: amount,
        start_date: startDate || null,
      })
      onSuccess()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'שגיאה בהגדרת הקרן')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6" dir="rtl">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">הגדרת קרן</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              סכום חודשי לקרן (₪)
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={e => setAmount(parseFloat(e.target.value) || 0)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              תאריך התחלה
            </label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'שומר...' : 'הגדר קרן'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              דלג
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default FundSetupModal
