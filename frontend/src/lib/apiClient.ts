/**
 * Typed API client wrappers.
 * All methods call the backend via the axios instance in `./api`.
 */
import api from './api'
import type {
  Project,
  ProjectCreate,
  ProjectWithFinance,
  Transaction,
  TransactionCreate,
  BudgetWithSpending,
  ExpenseCategory,
  RecurringTransactionTemplate,
  RecurringTransactionTemplateCreate,
  RecurringTransactionTemplateUpdate,
  RecurringTransactionInstanceUpdate,
  UnforeseenTransaction,
  DashboardSnapshot,
} from '../types/api'

// ─── Re-export useful types so consumers can import from apiClient ────────────

/** A category as returned by the categories list endpoint */
export interface Category {
  id: number
  name: string
  parent_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  children?: Category[]
}

/** A supplier as returned by the suppliers list endpoint */
export interface Supplier {
  id: number
  name: string
  contact_email?: string | null
  phone?: string | null
  annual_budget?: number | null
  category?: string | null
  category_id?: number | null
  is_active: boolean
  created_at: string
}

/** Quote subject */
export interface QuoteSubject {
  id: number
  address?: string | null
  num_apartments?: number | null
  num_buildings?: number | null
  notes?: string | null
  created_at: string
  updated_at: string
}

/** A quote project */
export interface QuoteProject {
  id: number
  name: string
  description?: string | null
  parent_id?: number | null
  project_id?: number | null
  quote_subject_id?: number | null
  expected_start_date?: string | null
  expected_income?: number | null
  expected_expenses?: number | null
  num_residents?: number | null
  status: string
  converted_project_id?: number | null
  created_at: string
  updated_at: string
  quote_lines?: QuoteLine[]
  children_count?: number
  quote_buildings?: unknown[]
  quote_subject?: QuoteSubject | null
}

/** A quote line */
export interface QuoteLine {
  id: number
  quote_project_id?: number | null
  quote_structure_item_id: number
  quote_structure_item_name?: string
  amount?: number | null
  sort_order: number
  created_at: string
}

/** A quote apartment (building level item) */
export interface QuoteApartment {
  id: number
  quote_building_id: number
  size: number
  count: number
  price_per_sqm?: number | null
  total_price?: number | null
  notes?: string | null
}

// ─── Dashboard API ────────────────────────────────────────────────────────────

export const DashboardAPI = {
  async getDashboardSnapshot(): Promise<DashboardSnapshot> {
    const { data } = await api.get<DashboardSnapshot>('/reports/dashboard-snapshot')
    return data
  },
}

// ─── Project API ──────────────────────────────────────────────────────────────

export const ProjectAPI = {
  async getProjects(params?: Record<string, unknown>): Promise<Project[]> {
    const { data } = await api.get<Project[]>('/projects', { params })
    return data
  },

  async getProject(id: number): Promise<Project> {
    const { data } = await api.get<Project>(`/projects/${id}`)
    return data
  },

  async getProjectFull(id: number, params?: Record<string, unknown>): Promise<ProjectWithFinance> {
    const { data } = await api.get<ProjectWithFinance>(`/projects/${id}/full`, { params })
    return data
  },

  async createProject(payload: ProjectCreate): Promise<Project> {
    const { data } = await api.post<Project>('/projects', payload)
    return data
  },

  async updateProject(id: number, payload: Partial<ProjectCreate>): Promise<Project> {
    const { data } = await api.put<Project>(`/projects/${id}`, payload)
    return data
  },

  async uploadProjectImage(id: number, file: File): Promise<Project> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<Project>(`/projects/${id}/upload-image`, formData)
    return data
  },

  async uploadProjectContract(id: number, file: File): Promise<Project> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<Project>(`/projects/${id}/upload-contract`, formData)
    return data
  },

  async checkProjectName(name: string, excludeId?: number): Promise<{ exists: boolean }> {
    const { data } = await api.get<{ exists: boolean }>('/projects/check-name', {
      params: { name, exclude_id: excludeId },
    })
    return data
  },

  async getContractPeriods(projectId: number): Promise<unknown[]> {
    const { data } = await api.get<unknown[]>(`/projects/${projectId}/contract-periods`)
    return data
  },

  async exportContractPeriodCSV(projectId: number, periodId: number): Promise<Blob> {
    const { data } = await api.get(`/projects/${projectId}/contract-periods/${periodId}/export-csv`, {
      responseType: 'blob',
    })
    return data
  },

  async exportContractYearCSV(projectId: number, year: number): Promise<Blob> {
    const { data } = await api.get(`/projects/${projectId}/contract-years/${year}/export-csv`, {
      responseType: 'blob',
    })
    return data
  },

  async getProjectTransactions(projectId: number, params?: Record<string, unknown>): Promise<Transaction[]> {
    const { data } = await api.get<Transaction[]>(`/projects/${projectId}/transactions`, { params })
    return data
  },
}

// ─── Transaction API ──────────────────────────────────────────────────────────

export const TransactionAPI = {
  async createTransaction(payload: TransactionCreate): Promise<Transaction> {
    const { data } = await api.post<Transaction>('/transactions', payload)
    return data
  },

  async updateTransaction(id: number, payload: Partial<TransactionCreate>): Promise<Transaction> {
    const { data } = await api.put<Transaction>(`/transactions/${id}`, payload)
    return data
  },

  async deleteTransaction(id: number): Promise<void> {
    await api.delete(`/transactions/${id}`)
  },

  async getTransactionDocuments(id: number): Promise<unknown[]> {
    const { data } = await api.get<unknown[]>(`/transactions/${id}/documents`)
    return data
  },

  async uploadTransactionDocument(id: number, file: File): Promise<unknown> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post(`/transactions/${id}/documents`, formData)
    return data
  },

  async deleteTransactionDocument(transactionId: number, documentId: number): Promise<void> {
    await api.delete(`/transactions/${transactionId}/documents/${documentId}`)
  },
}

// ─── Budget API ───────────────────────────────────────────────────────────────

export const BudgetAPI = {
  async getProjectBudgets(projectId: number): Promise<BudgetWithSpending[]> {
    const { data } = await api.get<BudgetWithSpending[]>(`/projects/${projectId}/budgets`)
    return data
  },
}

// ─── Category API ─────────────────────────────────────────────────────────────

export const CategoryAPI = {
  async getCategories(): Promise<Category[]> {
    const { data } = await api.get<Category[]>('/categories')
    return data
  },
}

// ─── Supplier API ─────────────────────────────────────────────────────────────

export const SupplierAPI = {
  async getSuppliers(params?: Record<string, unknown>): Promise<Supplier[]> {
    const { data } = await api.get<Supplier[]>('/suppliers', { params })
    return data
  },
}

// ─── Report API ───────────────────────────────────────────────────────────────

export const ReportAPI = {
  async generateReport(payload: Record<string, unknown>): Promise<Blob> {
    const { data } = await api.post('/reports/custom', payload, { responseType: 'blob' })
    return data
  },
}

// ─── Recurring Transaction API ────────────────────────────────────────────────

export const RecurringTransactionAPI = {
  async getProjectTemplates(projectId: number): Promise<RecurringTransactionTemplate[]> {
    const { data } = await api.get<RecurringTransactionTemplate[]>(
      `/projects/${projectId}/recurring-transactions`
    )
    return data
  },

  async createTemplate(payload: RecurringTransactionTemplateCreate): Promise<RecurringTransactionTemplate> {
    const { data } = await api.post<RecurringTransactionTemplate>('/recurring-transactions', payload)
    return data
  },

  async updateTemplate(id: number, payload: RecurringTransactionTemplateUpdate): Promise<RecurringTransactionTemplate> {
    const { data } = await api.put<RecurringTransactionTemplate>(`/recurring-transactions/${id}`, payload)
    return data
  },

  async deleteTemplate(id: number): Promise<void> {
    await api.delete(`/recurring-transactions/${id}`)
  },

  async deactivateTemplate(id: number): Promise<RecurringTransactionTemplate> {
    const { data } = await api.patch<RecurringTransactionTemplate>(
      `/recurring-transactions/${id}/deactivate`
    )
    return data
  },

  async getTemplateTransactions(id: number): Promise<Transaction[]> {
    const { data } = await api.get<Transaction[]>(`/recurring-transactions/${id}/transactions`)
    return data
  },

  async generateMonthlyTransactions(projectId: number): Promise<{ generated: number }> {
    const { data } = await api.post<{ generated: number }>(
      `/projects/${projectId}/recurring-transactions/generate`
    )
    return data
  },

  async ensureProjectTransactionsGenerated(projectId: number): Promise<void> {
    await api.post(`/projects/${projectId}/recurring-transactions/ensure-generated`)
  },

  async updateTransactionInstance(
    instanceId: number,
    payload: RecurringTransactionInstanceUpdate
  ): Promise<Transaction> {
    const { data } = await api.put<Transaction>(`/transactions/${instanceId}`, payload)
    return data
  },

  async deleteTransactionInstance(instanceId: number): Promise<void> {
    await api.delete(`/transactions/${instanceId}`)
  },
}

// ─── Unforeseen Transaction API ───────────────────────────────────────────────

export const UnforeseenTransactionAPI = {
  async executeUnforeseenTransaction(id: number): Promise<unknown> {
    const { data } = await api.post(`/unforeseen-transactions/${id}/execute`)
    return data
  },

  async updateUnforeseenTransaction(
    id: number,
    payload: Partial<UnforeseenTransaction>
  ): Promise<UnforeseenTransaction> {
    const { data } = await api.put<UnforeseenTransaction>(`/unforeseen-transactions/${id}`, payload)
    return data
  },
}

// ─── Quote Subjects API ───────────────────────────────────────────────────────

export const QuoteSubjectsAPI = {
  async create(payload: Partial<QuoteSubject>): Promise<QuoteSubject> {
    const { data } = await api.post<QuoteSubject>('/quote-subjects', payload)
    return data
  },

  async update(id: number, payload: Partial<QuoteSubject>): Promise<QuoteSubject> {
    const { data } = await api.put<QuoteSubject>(`/quote-subjects/${id}`, payload)
    return data
  },

  async deleteWithPassword(id: number, password: string): Promise<void> {
    await api.delete(`/quote-subjects/${id}`, { data: { password } })
  },
}
