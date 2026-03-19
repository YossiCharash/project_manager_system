// ─── Core domain types matching backend Pydantic schemas ───────────────────

export interface Project {
  id: number
  name: string
  description?: string | null
  start_date?: string | null
  end_date?: string | null
  contract_duration_months?: number | null
  budget_monthly: number
  budget_annual: number
  manager_id?: number | null
  relation_project?: number | null
  num_residents?: number | null
  monthly_price_per_apartment?: number | null
  address?: string | null
  city?: string | null
  image_url?: string | null
  is_parent_project: boolean
  show_in_quotes_tab: boolean
  contract_file_url?: string | null
  has_fund: boolean
  monthly_fund_amount?: number | null
  is_active: boolean
  created_at: string
  total_value: number
  first_contract_start_date?: string | null
}

export interface ProjectWithFinance extends Project {
  /** Total income for the project */
  total_income: number
  /** Total expense for the project */
  total_expense: number
  /** Net profit (income - expense) */
  profit: number
  /** Profit as a percentage of income */
  profit_percent: number
  /** Month-to-date income */
  income_month_to_date: number
  /** Month-to-date expense */
  expense_month_to_date: number
  /** Status color derived from financial health */
  status_color: 'green' | 'yellow' | 'red'
  /** Child projects (for parent projects) */
  children?: ProjectWithFinance[]
  /** Category breakdown of expenses */
  category_expenses?: { category: string; total: number }[]
}

export interface ProjectCreate {
  name: string
  description?: string | null
  start_date?: string | null
  end_date?: string | null
  contract_duration_months?: number | null
  budget_monthly?: number
  budget_annual?: number
  manager_id?: number | null
  relation_project?: number | null
  num_residents?: number | null
  monthly_price_per_apartment?: number | null
  address?: string | null
  city?: string | null
  image_url?: string | null
  is_parent_project?: boolean
  show_in_quotes_tab?: boolean
  contract_file_url?: string | null
  has_fund?: boolean
  monthly_fund_amount?: number | null
}

// ─── Transaction ────────────────────────────────────────────────────────────

export interface Transaction {
  id: number
  project_id: number
  tx_date: string
  type: 'Income' | 'Expense'
  amount: number
  description?: string | null
  category?: string | null
  category_id?: number | null
  payment_method?: string | null
  notes?: string | null
  is_exceptional: boolean
  is_generated: boolean
  file_path?: string | null
  supplier_id?: number | null
  created_by_user_id?: number | null
  created_at: string
  created_by_user?: Record<string, unknown> | null
  from_fund: boolean
  recurring_template_id?: number | null
  period_start_date?: string | null
  period_end_date?: string | null
}

export interface TransactionCreate {
  project_id: number
  tx_date: string
  type: 'Income' | 'Expense'
  amount: number
  description?: string | null
  category_id?: number | null
  payment_method?: string | null
  notes?: string | null
  is_exceptional?: boolean
  supplier_id?: number | null
  from_fund?: boolean
  allow_duplicate?: boolean
  allow_overlap?: boolean
  period_start_date?: string | null
  period_end_date?: string | null
}

// ─── Budget ─────────────────────────────────────────────────────────────────

export interface BudgetCreate {
  category_id: number
  amount: number
  period_type?: string
  start_date?: string | null
  end_date?: string | null
}

export interface BudgetWithSpending {
  id: number
  project_id: number
  contract_period_id?: number | null
  category: string
  amount: number
  base_amount: number
  period_type: string
  start_date: string
  end_date?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  spent_amount: number
  expense_amount: number
  income_amount: number
  remaining_amount: number
  spent_percentage: number
  expected_spent_percentage: number
  is_over_budget: boolean
  is_spending_too_fast: boolean
}

// ─── Category ────────────────────────────────────────────────────────────────

export interface ExpenseCategory {
  id: number
  name: string
  parent_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  children?: ExpenseCategory[]
}

// ─── Recurring Transactions ──────────────────────────────────────────────────

export interface RecurringTransactionTemplate {
  id: number
  project_id: number
  description: string
  type: 'Income' | 'Expense'
  amount: number
  category?: string | null
  category_id?: number | null
  notes?: string | null
  supplier_id?: number | null
  payment_method?: string | null
  frequency: 'Monthly'
  day_of_month: number
  start_date: string
  end_type: 'No End' | 'After Occurrences' | 'On Date'
  end_date?: string | null
  max_occurrences?: number | null
  is_active: boolean
  created_by_user_id?: number | null
  created_by_user?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface RecurringTransactionTemplateCreate {
  project_id: number
  description: string
  type: 'Income' | 'Expense'
  amount: number
  category_id?: number | null
  category?: string | null
  notes?: string | null
  supplier_id?: number | null
  payment_method?: string | null
  frequency?: 'Monthly'
  day_of_month: number
  start_date: string
  end_type?: 'No End' | 'After Occurrences' | 'On Date'
  end_date?: string | null
  max_occurrences?: number | null
}

export interface RecurringTransactionTemplateUpdate {
  description?: string | null
  amount?: number | null
  category_id?: number | null
  notes?: string | null
  supplier_id?: number | null
  payment_method?: string | null
  day_of_month?: number | null
  start_date?: string | null
  end_type?: 'No End' | 'After Occurrences' | 'On Date' | null
  end_date?: string | null
  max_occurrences?: number | null
  is_active?: boolean | null
}

export interface RecurringTransactionInstanceUpdate {
  tx_date?: string | null
  amount?: number | null
  category_id?: number | null
  notes?: string | null
}

// ─── Unforeseen Transactions ─────────────────────────────────────────────────

export interface UnforeseenTransaction {
  id: number
  project_id: number
  contract_period_id?: number | null
  status: string
  description?: string | null
  notes?: string | null
  transaction_date: string
  created_at: string
  updated_at: string
}

// ─── Notifications ───────────────────────────────────────────────────────────

export type NotificationType = 'instruction' | 'task_assignment' | 'task_reminder' | 'general'

export interface Notification {
  id: number
  user_id: number
  from_user_id?: number | null
  task_id?: number | null
  type: string
  title: string
  body?: string | null
  read_at?: string | null
  created_at: string
  from_user_name?: string | null
  task_title?: string | null
}

// ─── Dashboard Snapshot ──────────────────────────────────────────────────────

export interface DashboardSnapshot {
  projects: ProjectWithFinance[]
  alerts: {
    budget_overrun: ProjectWithFinance[]
    missing_proof: Transaction[]
    unpaid_recurring: RecurringTransactionTemplate[]
  }
  summary: {
    total_income: number
    total_expense: number
    total_profit: number
  }
}
