export interface DashboardOverview {
  tasks?: {
    total?: number;
    open?: number;
    completed?: number;
  };
  notes?: {
    total?: number;
  };
  finances?: {
    balance?: number;
    income?: number;
    expense?: number;
  };
  debts?: {
    openAmount?: number;
    count?: number;
  };
  reminders?: {
    scheduled?: number;
    nextTriggerAt?: string | null;
  };
  personal?: {
    total?: number;
  };
}

export interface DashboardStatistics {
  tasks: {
    createdLast7: number;
    completedLast7: number;
  };
  finances: {
    incomeLast7: number;
    expenseLast7: number;
    topCategoriesLast7: Array<{
      category_id: string | null;
      category_name: string;
      total: number;
    }>;
  };
  personal: {
    createdLast7: number;
    favorites: number;
  };
  reminders: {
    upcoming7Days: number;
  };
}

export type TaskStatus = 'new' | 'in_progress' | 'waiting' | 'completed' | 'cancelled';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export interface TaskSummary {
  id: string;
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority?: TaskPriority | null;
  deadline?: string | null;
  estimated_hours?: number | null;
  actual_hours?: number | null;
  project_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface NoteSummary {
  id: string;
  title?: string | null;
  content: string;
  content_format?: string;
  folder_id?: string | null;
  is_favorite?: boolean;
  is_archived?: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FinanceAccount {
  id: string;
  name: string;
  balance: number;
  currency: string;
  institution?: string | null;
}

export interface FinanceCategory {
  id: string;
  name: string;
  budget?: number | null;
  total_spent?: number | null;
}

export interface FinanceRule {
  id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  category_id?: string | null;
}

export interface FinanceTransaction {
  id: string;
  amount: number;
  currency: string;
  category_id?: string | null;
  account_id?: string | null;
  occurred_at: string;
  description?: string | null;
  type?: 'income' | 'expense';
}

export interface DebtSummary {
  id: string;
  counterparty: string;
  amount: number;
  currency: string;
  status: 'open' | 'closed';
  due_date?: string | null;
}

export interface ReminderSummary {
  id: string;
  title: string;
  reminder_time: string;
  timezone: string;
  status: 'scheduled' | 'done' | 'cancelled';
  recurrence_rule?: string | null;
  payload?: Record<string, unknown> | null;
}

export interface PersonalCategory {
  id: string;
  name: string;
  description?: string | null;
  color?: string | null;
  icon?: string | null;
  is_confidential?: boolean;
}

export interface PersonalEntry {
  id: string;
  category_id?: string | null;
  title: string;
  data_type: 'login' | 'contact' | 'document' | 'other';
  login_username?: string | null;
  login_password?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  document_number?: string | null;
  document_expiry?: string | null;
  custom_fields?: Record<string, unknown> | null;
  tags?: string[] | null;
  notes?: string | null;
  is_favorite?: boolean;
  is_confidential?: boolean;
}

export interface UserAssistantSettings {
  pinEnabled?: boolean;
  currentTone?: string | null;
}

export interface DashboardSummaryResponse {
  overview: DashboardOverview | null;
  tasks: TaskSummary[];
  notes: NoteSummary[];
  finances: FinanceTransaction[];
  financeAccounts: FinanceAccount[];
  financeCategories: FinanceCategory[];
  financeCategoryRules: FinanceRule[];
  debts: DebtSummary[];
  reminders: ReminderSummary[];
  personalEntries: PersonalEntry[];
  personalCategories?: PersonalCategory[];
  userSettings?: UserAssistantSettings | null;
  statistics?: DashboardStatistics;
}

export interface ToneOption {
  key: string;
  label: string;
}
