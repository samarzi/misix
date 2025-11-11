import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createAccount,
  createCategory,
  createRule,
  createTransaction,
  deleteAccount,
  deleteCategory,
  deleteRule,
  deleteTransaction,
  fetchDashboardSummary,
  updateAccount,
  updateCategory,
  updateRule,
  updateTransaction,
  createReminder,
  updateReminder,
  cancelReminder,
  createPersonalCategory,
  updatePersonalCategory,
  deletePersonalCategory,
  createPersonalEntry,
  updatePersonalEntry,
  deletePersonalEntry,
  createTask,
  updateTask,
  deleteTask,
  createNote,
  updateNote,
  deleteNote,
} from './client';
import type {
  DashboardSummaryResponse,
  FinanceAccount,
  FinanceCategory,
  FinanceRule,
} from './types';
import type { ReminderSummary, PersonalEntry } from './types';

const DASHBOARD_QUERY_KEY = ['dashboard'];

export const useDashboardQuery = (userId: string) =>
  useQuery({
    queryKey: [...DASHBOARD_QUERY_KEY, userId],
    queryFn: () => fetchDashboardSummary(userId),
    staleTime: 60_000,
  });

export const useCreateTransaction = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTransaction,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          finances: [data, ...prev.finances],
        };
      });
      queryClient.invalidateQueries({ queryKey: [...DASHBOARD_QUERY_KEY, userId] });
    },
  });
};

export const useCreateTask = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTask,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          tasks: [data, ...prev.tasks],
        };
      });
    },
  });
};

export const useUpdateTask = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTask,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          tasks: prev.tasks.map((task) => (task.id === data.id ? data : task)),
        };
      });
    },
  });
};

export const useDeleteTask = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTask,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          tasks: prev.tasks.filter((task) => task.id !== id),
        };
      });
    },
  });
};

export const useCreateNote = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createNote,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          notes: [data, ...prev.notes],
        };
      });
    },
  });
};

export const useUpdateNote = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateNote,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          notes: prev.notes.map((note) => (note.id === data.id ? data : note)),
        };
      });
    },
  });
};

export const useDeleteNote = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteNote,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          notes: prev.notes.filter((note) => note.id !== id),
        };
      });
    },
  });
};

export const useUpdateTransaction = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTransaction,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          finances: prev.finances.map((tx) => (tx.id === data.id ? data : tx)),
        };
      });
    },
  });
};

export const useDeleteTransaction = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTransaction,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          finances: prev.finances.filter((tx) => tx.id !== id),
        };
      });
    },
  });
};

const upsertEntity = <T extends { id: string }>(list: T[], payload: T) => {
  const exists = list.some((item) => item.id === payload.id);
  if (exists) {
    return list.map((item) => (item.id === payload.id ? payload : item));
  }
  return [payload, ...list];
};

export const useCreateAccount = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAccount,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeAccounts: upsertEntity<FinanceAccount>(prev.financeAccounts, data),
        };
      });
    },
  });
};

export const useUpdateAccount = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateAccount,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeAccounts: upsertEntity(prev.financeAccounts, data),
        };
      });
    },
  });
};

export const useDeleteAccount = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAccount,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeAccounts: prev.financeAccounts.filter((account) => account.id !== id),
        };
      });
    },
  });
};

export const useCreateCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCategory,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategories: upsertEntity<FinanceCategory>(prev.financeCategories, data),
        };
      });
    },
  });
};

export const useUpdateCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateCategory,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategories: upsertEntity(prev.financeCategories, data),
        };
      });
    },
  });
};

export const useDeleteCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCategory,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategories: prev.financeCategories.filter((category) => category.id !== id),
        };
      });
    },
  });
};

export const useCreateRule = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRule,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategoryRules: upsertEntity<FinanceRule>(prev.financeCategoryRules, data),
        };
      });
    },
  });
};

export const useUpdateRule = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateRule,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategoryRules: upsertEntity(prev.financeCategoryRules, data),
        };
      });
    },
  });
};

export const useDeleteRule = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteRule,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          financeCategoryRules: prev.financeCategoryRules.filter((rule) => rule.id !== id),
        };
      });
    },
  });
};

const sortReminders = (reminders: ReminderSummary[]) =>
  reminders.slice().sort((a, b) => new Date(b.reminder_time).getTime() - new Date(a.reminder_time).getTime());

export const useCreateReminder = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createReminder,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          reminders: sortReminders([data, ...prev.reminders]),
        };
      });
    },
  });
};

export const useUpdateReminder = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateReminder,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          reminders: sortReminders(prev.reminders.map((item) => (item.id === data.id ? data : item))),
        };
      });
    },
  });
};

export const useCancelReminder = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: cancelReminder,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          reminders: prev.reminders.map((item) =>
            item.id === id ? { ...item, status: 'cancelled' as ReminderSummary['status'] } : item,
          ),
        };
      });
    },
  });
};

export const useCreatePersonalCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPersonalCategory,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        const categories = prev.personalCategories ?? [];
        return {
          ...prev,
          personalCategories: [data, ...categories],
        };
      });
    },
  });
};

export const useUpdatePersonalCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updatePersonalCategory,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        const categories = prev.personalCategories ?? [];
        return {
          ...prev,
          personalCategories: categories.map((category) => (category.id === data.id ? data : category)),
        };
      });
    },
  });
};

export const useDeletePersonalCategory = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deletePersonalCategory,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        const categories = prev.personalCategories ?? [];
        return {
          ...prev,
          personalCategories: categories.filter((category) => category.id !== id),
          personalEntries: prev.personalEntries.map((entry) =>
            entry.category_id === id ? { ...entry, category_id: null } : entry,
          ),
        };
      });
    },
  });
};

const upsertPersonalEntry = (entries: PersonalEntry[], payload: PersonalEntry) => {
  const exists = entries.some((item) => item.id === payload.id);
  if (exists) {
    return entries.map((item) => (item.id === payload.id ? payload : item));
  }
  return [payload, ...entries];
};

export const useCreatePersonalEntry = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPersonalEntry,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          personalEntries: upsertPersonalEntry(prev.personalEntries, data),
        };
      });
    },
  });
};

export const useUpdatePersonalEntry = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updatePersonalEntry,
    onSuccess: (data) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          personalEntries: upsertPersonalEntry(prev.personalEntries, data),
        };
      });
    },
  });
};

export const useDeletePersonalEntry = (userId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deletePersonalEntry,
    onSuccess: (_, id) => {
      queryClient.setQueryData<DashboardSummaryResponse>([...DASHBOARD_QUERY_KEY, userId], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          personalEntries: prev.personalEntries.filter((entry) => entry.id !== id),
        };
      });
    },
  });
};
