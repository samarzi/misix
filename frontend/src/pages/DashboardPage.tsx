import { useEffect, useMemo, useState } from 'react';
import AppLayout from '../components/AppLayout';
import Toolbar from '../components/Toolbar';
import SummaryCard from '../components/SummaryCard';
import Button from '../components/Button';
import Loader from '../components/Loader';
import SectionHeader from '../components/SectionHeader';
import Modal from '../components/Modal';
import PinLock from '../features/pin/PinLock';
import AnalyticsDetail from '../features/analytics/AnalyticsDetail';
import TasksDetail from '../features/tasks/TasksDetail';
import NotesDetail from '../features/notes/NotesDetail';
import TaskForm, { type TaskFormValues } from '../features/tasks/TaskForm';
import NoteForm, { type NoteFormValues } from '../features/notes/NoteForm';
import FinancesDetail from '../features/finances/FinancesDetail';
import DebtsDetail from '../features/debts/DebtsDetail';
import RemindersDetail from '../features/reminders/RemindersDetail';
import ReminderForm from '../features/reminders/ReminderForm';
import PersonalDetail from '../features/personal/PersonalDetail';
import FinanceTransactionForm from '../features/finances/components/FinanceTransactionForm';
import FinanceAccountForm from '../features/finances/components/FinanceAccountForm';
import FinanceCategoryForm from '../features/finances/components/FinanceCategoryForm';
import FinanceRuleForm from '../features/finances/components/FinanceRuleForm';
import PersonalCategoryForm from '../features/personal/PersonalCategoryForm';
import PersonalEntryForm, { type PersonalEntrySubmitValues } from '../features/personal/PersonalEntryForm';
import EmptyState from '../components/EmptyState';
import {
  useCreateAccount,
  useCreateCategory,
  useCreateRule,
  useCreateTransaction,
  useCreateReminder,
  useDashboardQuery,
  useDeleteAccount,
  useDeleteCategory,
  useDeleteRule,
  useDeleteTransaction,
  useCancelReminder,
  useUpdateAccount,
  useUpdateCategory,
  useUpdateRule,
  useUpdateTransaction,
  useUpdateReminder,
  useCreatePersonalCategory,
  useUpdatePersonalCategory,
  useDeletePersonalCategory,
  useCreatePersonalEntry,
  useUpdatePersonalEntry,
  useDeletePersonalEntry,
  useCreateTask,
  useUpdateTask,
  useDeleteTask,
  useCreateNote,
  useUpdateNote,
  useDeleteNote,
} from '../api/hooks';
import { useUiStore } from '../stores/uiStore';
import { resolveUserId } from '../utils/user';
import { getEmptyStateMessage, getToneGreeting } from '../utils/tone';
import { formatAmount, formatNumber } from '../utils/format';
import { MISIX_TONE_STYLES, type ToneStyle } from '../config';
import type {
  CreateAccountPayload,
  CreateCategoryPayload,
  CreateRulePayload,
  CreateTransactionPayload,
  CreateReminderPayload,
  UpdateAccountPayload,
  UpdateCategoryPayload,
  UpdateRulePayload,
  UpdateTransactionPayload,
  UpdateReminderPayload,
  CreatePersonalCategoryPayload,
  UpdatePersonalCategoryPayload,
  CreatePersonalEntryPayload,
  UpdatePersonalEntryPayload,
  CreateTaskPayload,
  UpdateTaskPayload,
  CreateNotePayload,
  UpdateNotePayload,
} from '../api/client';
import type { TaskPriority, TaskStatus } from '../api/types';

const DashboardPage = () => {
  const userId = useMemo(() => resolveUserId(), []);
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useDashboardQuery(userId);

  const [modalError, setModalError] = useState<string | null>(null);
  const [taskStatusFilter, setTaskStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [taskPriorityFilter, setTaskPriorityFilter] = useState<TaskPriority | 'all'>('all');
  const [noteSearch, setNoteSearch] = useState('');

  const filteredTasks = useMemo(() => {
    if (!data) return [];
    return data.tasks.filter((task) => {
      const matchesStatus = taskStatusFilter === 'all' || task.status === taskStatusFilter;
      const matchesPriority = taskPriorityFilter === 'all' || task.priority === taskPriorityFilter;
      return matchesStatus && matchesPriority;
    });
  }, [data, taskStatusFilter, taskPriorityFilter]);

  const filteredNotes = useMemo(() => {
    if (!data) return [];
    const query = noteSearch.trim().toLowerCase();
    if (!query) return data.notes;
    return data.notes.filter((note) => {
      const title = note.title?.toLowerCase() ?? '';
      const content = note.content.toLowerCase();
      return title.includes(query) || content.includes(query);
    });
  }, [data, noteSearch]);

  const {
    view,
    section,
    setSection,
    setView,
    financeTab,
    setFinanceTab,
    tone,
    setTone,
    modal,
    openModal,
    closeModal,
    pin,
    setPinState,
    showToast,
  } = useUiStore();

  useEffect(() => {
    const pinEnabled = Boolean(data?.userSettings?.pinEnabled);
    if (pinEnabled && !pin.enabled) {
      setPinState({ enabled: true, locked: true, error: null });
    }
    if (!pinEnabled && pin.enabled) {
      setPinState({ enabled: false, locked: false, error: null });
    }
  }, [data?.userSettings?.pinEnabled, pin.enabled, setPinState]);

  useEffect(() => {
    const backendTone = data?.userSettings?.currentTone;
    if (backendTone && MISIX_TONE_STYLES.some((item) => item.key === backendTone) && !tone) {
      setTone(backendTone as ToneStyle);
    }
  }, [data?.userSettings?.currentTone, setTone, tone]);

  const handleUnlock = async () => {
    setPinState({ locked: false, error: null });
  };

  const handleResetPin = () => {
    setPinState({ locked: false, enabled: false, error: null });
  };

  const greeting = getToneGreeting((tone as ToneStyle) ?? 'teasing', data?.overview);

  const summaryCards = useMemo(() => {
    const overview = data?.overview;
    return [
      {
        key: 'analytics',
        icon: '📊',
        title: 'Аналитика',
        primary: overview?.finances?.balance != null ? formatAmount(overview.finances.balance) : 'Нет данных',
        secondary: 'Глубокие показатели',
      },
      {
        key: 'tasks',
        icon: '🗂️',
        title: 'Задачи',
        primary: formatNumber(overview?.tasks?.total ?? data?.tasks.length ?? 0),
        secondary: `${formatNumber(overview?.tasks?.open ?? 0)} в работе · ${formatNumber(overview?.tasks?.completed ?? 0)} готово`,
      },
      {
        key: 'notes',
        icon: '📝',
        title: 'Заметки',
        primary: formatNumber(overview?.notes?.total ?? data?.notes.length ?? 0),
        secondary: `${formatNumber(overview?.personal?.total ?? 0)} личных записей`,
      },
      {
        key: 'finances',
        icon: '💰',
        title: 'Финансы',
        primary: overview?.finances?.income != null ? formatAmount(overview.finances.income) : formatAmount(0),
        secondary: `Расходы ${formatAmount(overview?.finances?.expense ?? 0)}`,
      },
      {
        key: 'debts',
        icon: '📉',
        title: 'Долги',
        primary: formatAmount(overview?.debts?.openAmount ?? 0),
        secondary: `${formatNumber(overview?.debts?.count ?? data?.debts.length ?? 0)} активных`,
      },
      {
        key: 'reminders',
        icon: '⏰',
        title: 'Напоминания',
        primary: formatNumber(overview?.reminders?.scheduled ?? data?.reminders.length ?? 0),
        secondary: overview?.reminders?.nextTriggerAt ? `Следующее: ${new Date(overview.reminders.nextTriggerAt).toLocaleString('ru-RU')}` : 'Нет запланированных',
      },
    ];
  }, [data]);

  const createTransactionMutation = useCreateTransaction(userId);
  const updateTransactionMutation = useUpdateTransaction(userId);
  const deleteTransactionMutation = useDeleteTransaction(userId);
  const createAccountMutation = useCreateAccount(userId);
  const updateAccountMutation = useUpdateAccount(userId);
  const deleteAccountMutation = useDeleteAccount(userId);
  const createCategoryMutation = useCreateCategory(userId);
  const updateCategoryMutation = useUpdateCategory(userId);
  const deleteCategoryMutation = useDeleteCategory(userId);
  const createRuleMutation = useCreateRule(userId);
  const updateRuleMutation = useUpdateRule(userId);
  const deleteRuleMutation = useDeleteRule(userId);
  const createReminderMutation = useCreateReminder(userId);
  const updateReminderMutation = useUpdateReminder(userId);
  const cancelReminderMutation = useCancelReminder(userId);
  const createPersonalCategoryMutation = useCreatePersonalCategory(userId);
  const updatePersonalCategoryMutation = useUpdatePersonalCategory(userId);
  const deletePersonalCategoryMutation = useDeletePersonalCategory(userId);
  const createPersonalEntryMutation = useCreatePersonalEntry(userId);
  const updatePersonalEntryMutation = useUpdatePersonalEntry(userId);
  const deletePersonalEntryMutation = useDeletePersonalEntry(userId);
  const createTaskMutation = useCreateTask(userId);
  const updateTaskMutation = useUpdateTask(userId);
  const deleteTaskMutation = useDeleteTask(userId);
  const createNoteMutation = useCreateNote(userId);
  const updateNoteMutation = useUpdateNote(userId);
  const deleteNoteMutation = useDeleteNote(userId);

  const handleCreateTransaction = async (values: Parameters<typeof FinanceTransactionForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const normalizedAmount = values.type === 'expense' ? -Math.abs(values.amount) : Math.abs(values.amount);
    const payload: CreateTransactionPayload = {
      amount: normalizedAmount,
      account_id: values.account_id,
      category_id: values.category_id,
      description: values.description,
      occurred_at: values.occurred_at,
      currency: 'RUB',
      type: values.type,
    };
    await createTransactionMutation.mutateAsync(payload);
    showToast('Операция сохранена', 'success');
    closeModal();
  };

  const handleUpdateTransaction = async (transactionId: string, values: Parameters<typeof FinanceTransactionForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const normalizedAmount = values.type === 'expense' ? -Math.abs(values.amount) : Math.abs(values.amount);
    const payload: UpdateTransactionPayload = {
      id: transactionId,
      amount: normalizedAmount,
      account_id: values.account_id,
      category_id: values.category_id,
      description: values.description,
      occurred_at: values.occurred_at,
      type: values.type,
    };
    await updateTransactionMutation.mutateAsync(payload);
    showToast('Операция обновлена', 'success');
    closeModal();
  };

  const handleDeleteTransaction = async (transactionId: string) => {
    setModalError(null);
    await deleteTransactionMutation.mutateAsync(transactionId);
    showToast('Операция удалена', 'success');
    closeModal();
  };

  const handleCreateAccount = async (values: Parameters<typeof FinanceAccountForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: CreateAccountPayload = {
      name: values.name,
      balance: values.balance,
      currency: values.currency,
      institution: values.institution,
    };
    await createAccountMutation.mutateAsync(payload);
    showToast('Счёт создан', 'success');
    closeModal();
  };

  const handleUpdateAccount = async (accountId: string, values: Parameters<typeof FinanceAccountForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: UpdateAccountPayload = {
      id: accountId,
      name: values.name,
      balance: values.balance,
      currency: values.currency,
      institution: values.institution,
    };
    await updateAccountMutation.mutateAsync(payload);
    showToast('Счёт обновлён', 'success');
    closeModal();
  };

  const handleDeleteAccount = async (accountId: string) => {
    setModalError(null);
    await deleteAccountMutation.mutateAsync(accountId);
    showToast('Счёт удалён', 'success');
    closeModal();
  };

  const handleCreateCategory = async (values: Parameters<typeof FinanceCategoryForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: CreateCategoryPayload = {
      name: values.name,
      budget: values.budget ?? undefined,
    };
    await createCategoryMutation.mutateAsync(payload);
    showToast('Категория создана', 'success');
    closeModal();
  };

  const handleUpdateCategory = async (categoryId: string, values: Parameters<typeof FinanceCategoryForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: UpdateCategoryPayload = {
      id: categoryId,
      name: values.name,
      budget: values.budget ?? undefined,
    };
    await updateCategoryMutation.mutateAsync(payload);
    showToast('Категория обновлена', 'success');
    closeModal();
  };

  const handleDeleteCategory = async (categoryId: string) => {
    setModalError(null);
    await deleteCategoryMutation.mutateAsync(categoryId);
    showToast('Категория удалена', 'success');
    closeModal();
  };

  const handleCreateRule = async (values: Parameters<typeof FinanceRuleForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: CreateRulePayload = {
      name: values.name,
      description: values.description,
      is_active: values.is_active,
      category_id: values.category_id,
    };
    await createRuleMutation.mutateAsync(payload);
    showToast('Правило создано', 'success');
    closeModal();
  };

  const handleUpdateRule = async (ruleId: string, values: Parameters<typeof FinanceRuleForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: UpdateRulePayload = {
      id: ruleId,
      name: values.name,
      description: values.description,
      is_active: values.is_active,
      category_id: values.category_id,
    };
    await updateRuleMutation.mutateAsync(payload);
    showToast('Правило обновлено', 'success');
    closeModal();
  };

  const handleDeleteRule = async (ruleId: string) => {
    setModalError(null);
    await deleteRuleMutation.mutateAsync(ruleId);
    showToast('Правило удалено', 'success');
    closeModal();
  };

  const handleCreateReminder = async (values: Parameters<typeof ReminderForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: CreateReminderPayload = {
      title: values.title,
      reminder_time: values.reminder_time,
      timezone: values.timezone,
      status: values.status,
      recurrence_rule: values.recurrence_rule,
    };
    await createReminderMutation.mutateAsync(payload);
    showToast('Напоминание сохранено', 'success');
    closeModal();
  };

  const handleUpdateReminder = async (reminderId: string, values: Parameters<typeof ReminderForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: UpdateReminderPayload = {
      id: reminderId,
      title: values.title,
      reminder_time: values.reminder_time,
      timezone: values.timezone,
      status: values.status,
      recurrence_rule: values.recurrence_rule,
    };
    await updateReminderMutation.mutateAsync(payload);
    showToast('Напоминание обновлено', 'success');
    closeModal();
  };

  const handleCancelReminder = async (reminderId: string) => {
    setModalError(null);
    await cancelReminderMutation.mutateAsync(reminderId);
    showToast('Напоминание отменено', 'success');
    closeModal();
  };

  const handleCreatePersonalCategory = async (values: Parameters<typeof PersonalCategoryForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: CreatePersonalCategoryPayload = {
      name: values.name,
      description: values.description ?? null,
      color: values.color ?? null,
      icon: values.icon ?? null,
      is_confidential: values.is_confidential ?? false,
    };
    await createPersonalCategoryMutation.mutateAsync(payload);
    showToast('Категория сохранена', 'success');
    closeModal();
  };

  const handleUpdatePersonalCategory = async (categoryId: string, values: Parameters<typeof PersonalCategoryForm>[0]['onSubmit'] extends (value: infer V) => any ? V : never) => {
    setModalError(null);
    const payload: UpdatePersonalCategoryPayload = {
      id: categoryId,
      name: values.name,
      description: values.description ?? null,
      color: values.color ?? null,
      icon: values.icon ?? null,
      is_confidential: values.is_confidential ?? false,
    };
    await updatePersonalCategoryMutation.mutateAsync(payload);
    showToast('Категория обновлена', 'success');
    closeModal();
  };

  const handleDeletePersonalCategory = async (categoryId: string) => {
    setModalError(null);
    await deletePersonalCategoryMutation.mutateAsync(categoryId);
    showToast('Категория удалена', 'success');
    closeModal();
  };

  const handleCreatePersonalEntry = async (values: PersonalEntrySubmitValues) => {
    setModalError(null);
    const payload: CreatePersonalEntryPayload = {
      ...values,
      custom_fields: values.custom_fields ?? null,
      tags: values.tags ?? null,
    };
    await createPersonalEntryMutation.mutateAsync(payload);
    showToast('Запись сохранена', 'success');
    closeModal();
  };

  const handleUpdatePersonalEntry = async (entryId: string, values: PersonalEntrySubmitValues) => {
    setModalError(null);
    const payload: UpdatePersonalEntryPayload = {
      id: entryId,
      ...values,
      custom_fields: values.custom_fields ?? null,
      tags: values.tags ?? null,
    };
    await updatePersonalEntryMutation.mutateAsync(payload);
    showToast('Запись обновлена', 'success');
    closeModal();
  };

  const handleDeletePersonalEntry = async (entryId: string) => {
    setModalError(null);
    await deletePersonalEntryMutation.mutateAsync(entryId);
    showToast('Запись удалена', 'success');
    closeModal();
  };

  const handleCreateTask = async (values: TaskFormValues) => {
    setModalError(null);
    const payload: CreateTaskPayload = {
      title: values.title,
      description: values.description ?? undefined,
      priority: values.priority,
      status: values.status,
      deadline: values.deadline ?? undefined,
    };
    await createTaskMutation.mutateAsync(payload);
    showToast('Задача создана', 'success');
    closeModal();
  };

  const handleUpdateTask = async (taskId: string, values: TaskFormValues) => {
    setModalError(null);
    const payload: UpdateTaskPayload = {
      id: taskId,
      title: values.title,
      description: values.description ?? undefined,
      priority: values.priority,
      status: values.status,
      deadline: values.deadline ?? undefined,
    };
    await updateTaskMutation.mutateAsync(payload);
    showToast('Задача обновлена', 'success');
    closeModal();
  };

  const handleDeleteTask = async (taskId: string) => {
    setModalError(null);
    await deleteTaskMutation.mutateAsync(taskId);
    showToast('Задача удалена', 'success');
    closeModal();
  };

  const handleCreateNote = async (values: NoteFormValues) => {
    setModalError(null);
    const payload: CreateNotePayload = {
      title: values.title ?? undefined,
      content: values.content,
      content_format: values.content_format ?? 'markdown',
    };
    await createNoteMutation.mutateAsync(payload);
    showToast('Заметка создана', 'success');
    closeModal();
  };

  const handleUpdateNote = async (noteId: string, values: NoteFormValues) => {
    setModalError(null);
    const payload: UpdateNotePayload = {
      id: noteId,
      title: values.title ?? undefined,
      content: values.content,
      content_format: values.content_format ?? 'markdown',
    };
    await updateNoteMutation.mutateAsync(payload);
    showToast('Заметка обновлена', 'success');
    closeModal();
  };

  const handleDeleteNote = async (noteId: string) => {
    setModalError(null);
    await deleteNoteMutation.mutateAsync(noteId);
    showToast('Заметка удалена', 'success');
    closeModal();
  };

  const handleMutationError = (errorMessage: string) => {
    setModalError(errorMessage);
    showToast(errorMessage, 'error');
  };

  const renderModal = () => {
    if (!modal.type) return null;

    const accounts = data?.financeAccounts ?? [];
    const categories = data?.financeCategories ?? [];
    const reminder = modal.payload?.entityId
      ? data?.reminders.find((item) => item.id === modal.payload?.entityId)
      : undefined;
    const personalCategories = data?.personalCategories ?? [];
    const personalEntry = modal.payload?.entityId
      ? data?.personalEntries.find((item) => item.id === modal.payload?.entityId)
      : undefined;
    switch (modal.type) {
      case 'finance-transaction': {
        const transaction = modal.payload?.entityId
          ? data?.finances.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(modal.payload?.entityId);
        return (
          <Modal
            title={isEdit ? 'Редактировать операцию' : 'Добавить операцию'}
            onClose={closeModal}
            actions={null}
          >
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <FinanceTransactionForm
              defaultValues={transaction}
              accounts={accounts}
              categories={categories}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (isEdit && modal.payload?.entityId) {
                    await handleUpdateTransaction(modal.payload.entityId, values);
                  } else {
                    await handleCreateTransaction(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить операцию');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Добавить'}
            />
          </Modal>
        );
      }
      case 'finance-account': {
        const account = modal.payload?.entityId
          ? data?.financeAccounts.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(account);
        return (
          <Modal title={isEdit ? 'Редактировать счёт' : 'Добавить счёт'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <FinanceAccountForm
              defaultValues={account}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (account) {
                    await handleUpdateAccount(account.id, values);
                  } else {
                    await handleCreateAccount(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить счёт');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Добавить'}
            />
          </Modal>
        );
      }
      case 'finance-category': {
        const category = modal.payload?.entityId
          ? data?.financeCategories.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(category);
        return (
          <Modal title={isEdit ? 'Редактировать категорию' : 'Добавить категорию'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <FinanceCategoryForm
              defaultValues={category}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (category) {
                    await handleUpdateCategory(category.id, values);
                  } else {
                    await handleCreateCategory(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить категорию');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Добавить'}
            />
          </Modal>
        );
      }
      case 'finance-rule': {
        const rule = modal.payload?.entityId
          ? data?.financeCategoryRules.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(rule);
        return (
          <Modal title={isEdit ? 'Редактировать правило' : 'Создать правило'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <FinanceRuleForm
              defaultValues={rule ?? undefined}
              categories={categories}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (rule) {
                    await handleUpdateRule(rule.id, values);
                  } else {
                    await handleCreateRule(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить правило');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Добавить'}
            />
          </Modal>
        );
      }
      case 'finance-delete-account': {
        const account = modal.payload?.entityId
          ? data?.financeAccounts.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!account) return null;
        return (
          <Modal title="Удалить счёт" onClose={closeModal}>
            <p className="text-sm text-text">Вы уверены, что хотите удалить счёт «{account.name}»?</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteAccount(account.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить счёт');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'finance-delete-category': {
        const category = modal.payload?.entityId
          ? data?.financeCategories.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!category) return null;
        return (
          <Modal title="Удалить категорию" onClose={closeModal}>
            <p className="text-sm text-text">Удалить категорию «{category.name}»? Связанные операции останутся.</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteCategory(category.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить категорию');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'finance-delete-rule': {
        const rule = modal.payload?.entityId
          ? data?.financeCategoryRules.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!rule) return null;
        return (
          <Modal title="Удалить правило" onClose={closeModal}>
            <p className="text-sm text-text">Удалить правило «{rule.name}»?</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteRule(rule.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить правило');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'finance-delete-transaction': {
        const transaction = modal.payload?.entityId
          ? data?.finances.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!transaction) return null;
        return (
          <Modal title="Удалить операцию" onClose={closeModal}>
            <p className="text-sm text-text">
              Удалить операцию «{transaction.description ?? 'Операция'}» от {new Date(transaction.occurred_at).toLocaleString('ru-RU')}?
            </p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteTransaction(transaction.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить операцию');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'reminder': {
        const isEdit = Boolean(reminder);
        return (
          <Modal title={isEdit ? 'Редактировать напоминание' : 'Создать напоминание'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <ReminderForm
              defaultValues={reminder}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (reminder) {
                    await handleUpdateReminder(reminder.id, values);
                  } else {
                    await handleCreateReminder(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить напоминание');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Создать'}
            />
          </Modal>
        );
      }
      case 'reminder-cancel': {
        if (!reminder) return null;
        return (
          <Modal title="Отменить напоминание" onClose={closeModal}>
            <p className="text-sm text-text">
              Отменить напоминание «{reminder.title}»?
            </p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Назад
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleCancelReminder(reminder.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось отменить напоминание');
                  }
                }}
              >
                Отменить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'personal-category': {
        const category = modal.payload?.entityId
          ? personalCategories.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(category);
        return (
          <Modal title={isEdit ? 'Редактировать категорию' : 'Создать категорию'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <PersonalCategoryForm
              defaultValues={category}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (category) {
                    await handleUpdatePersonalCategory(category.id, values);
                  } else {
                    await handleCreatePersonalCategory(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить категорию');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Создать'}
            />
          </Modal>
        );
      }
      case 'personal-delete-category': {
        const category = modal.payload?.entityId
          ? personalCategories.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!category) return null;
        return (
          <Modal title="Удалить категорию" onClose={closeModal}>
            <p className="text-sm text-text">Удалить категорию «{category.name}»? Записи останутся без категории.</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeletePersonalCategory(category.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить категорию');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'personal-entry': {
        const isEdit = Boolean(personalEntry);
        return (
          <Modal title={isEdit ? 'Редактировать запись' : 'Создать запись'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <PersonalEntryForm
              defaultValues={personalEntry}
              categories={personalCategories}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (personalEntry) {
                    await handleUpdatePersonalEntry(personalEntry.id, values);
                  } else {
                    await handleCreatePersonalEntry(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить запись');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Создать'}
            />
          </Modal>
        );
      }
      case 'personal-delete-entry': {
        if (!personalEntry) return null;
        return (
          <Modal title="Удалить запись" onClose={closeModal}>
            <p className="text-sm text-text">Удалить запись «{personalEntry.title}»?</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeletePersonalEntry(personalEntry.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить запись');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'task': {
        const task = modal.payload?.entityId
          ? data?.tasks.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(task);
        return (
          <Modal title={isEdit ? 'Редактировать задачу' : 'Создать задачу'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <TaskForm
              defaultValues={task}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (task) {
                    await handleUpdateTask(task.id, values);
                  } else {
                    await handleCreateTask(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить задачу');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Создать'}
            />
          </Modal>
        );
      }
      case 'task-delete': {
        const task = modal.payload?.entityId
          ? data?.tasks.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!task) return null;
        return (
          <Modal title="Удалить задачу" onClose={closeModal}>
            <p className="text-sm text-text">Удалить задачу «{task.title}»?</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteTask(task.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить задачу');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      case 'note': {
        const note = modal.payload?.entityId
          ? data?.notes.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        const isEdit = Boolean(note);
        return (
          <Modal title={isEdit ? 'Редактировать заметку' : 'Создать заметку'} onClose={closeModal} actions={null}>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <NoteForm
              defaultValues={note}
              onCancel={closeModal}
              onSubmit={async (values) => {
                try {
                  if (note) {
                    await handleUpdateNote(note.id, values);
                  } else {
                    await handleCreateNote(values);
                  }
                } catch (mutationError) {
                  console.error(mutationError);
                  handleMutationError('Не удалось сохранить заметку');
                }
              }}
              submitLabel={isEdit ? 'Сохранить изменения' : 'Создать'}
            />
          </Modal>
        );
      }
      case 'note-delete': {
        const note = modal.payload?.entityId
          ? data?.notes.find((item) => item.id === modal.payload?.entityId)
          : undefined;
        if (!note) return null;
        return (
          <Modal title="Удалить заметку" onClose={closeModal}>
            <p className="text-sm text-text">Удалить заметку «{note.title ?? 'Без названия'}»?</p>
            {modalError && <p className="text-sm text-danger">{modalError}</p>}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={closeModal}>
                Отмена
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  try {
                    await handleDeleteNote(note.id);
                  } catch (mutationError) {
                    console.error(mutationError);
                    handleMutationError('Не удалось удалить заметку');
                  }
                }}
              >
                Удалить
              </Button>
            </div>
          </Modal>
        );
      }
      default:
        return null;
    }
  };

  const renderDetail = () => {
    if (!data) {
      return <EmptyState title="Нет данных" description="Попробуй обновить дашборд." />;
    }

    switch (section) {
      case 'analytics':
        return (
          <AnalyticsDetail
            overview={data.overview}
            finances={data.finances}
            accounts={data.financeAccounts}
            categories={data.financeCategories}
            statistics={data.statistics}
          />
        );
      case 'tasks':
        return (
          <TasksDetail
            tasks={filteredTasks}
            tone={tone as ToneStyle}
            onCreate={() => openModal('task')}
            onEdit={(id) => openModal('task', { entityId: id })}
            onDelete={(id) => openModal('task-delete', { entityId: id })}
            statusFilter={taskStatusFilter}
            priorityFilter={taskPriorityFilter}
            onStatusFilterChange={setTaskStatusFilter}
            onPriorityFilterChange={setTaskPriorityFilter}
          />
        );
      case 'notes':
        return (
          <NotesDetail
            notes={filteredNotes}
            tone={tone as ToneStyle}
            onCreate={() => openModal('note')}
            onEdit={(id) => openModal('note', { entityId: id })}
            onDelete={(id) => openModal('note-delete', { entityId: id })}
            searchValue={noteSearch}
            onSearchChange={setNoteSearch}
          />
        );
      case 'finances':
        return (
          <FinancesDetail
            transactions={data.finances}
            accounts={data.financeAccounts}
            categories={data.financeCategories}
            rules={data.financeCategoryRules}
            activeTab={financeTab}
            onTabChange={setFinanceTab}
            onCreateTransaction={() => openModal('finance-transaction')}
            onEditTransaction={(id) => openModal('finance-transaction', { entityId: id })}
            onDeleteTransaction={(id) => openModal('finance-delete-transaction', { entityId: id })}
            onCreateAccount={() => openModal('finance-account')}
            onEditAccount={(id) => openModal('finance-account', { entityId: id })}
            onDeleteAccount={(id) => openModal('finance-delete-account', { entityId: id })}
            onCreateCategory={() => openModal('finance-category')}
            onEditCategory={(id) => openModal('finance-category', { entityId: id })}
            onDeleteCategory={(id) => openModal('finance-delete-category', { entityId: id })}
            onCreateRule={() => openModal('finance-rule')}
            onEditRule={(id) => openModal('finance-rule', { entityId: id })}
            onDeleteRule={(id) => openModal('finance-delete-rule', { entityId: id })}
            emptyDescription={getEmptyStateMessage(tone as ToneStyle, 'Финансы')}
          />
        );
      case 'debts':
        return <DebtsDetail debts={data.debts} tone={tone as ToneStyle} />;
      case 'reminders':
        return (
          <RemindersDetail
            reminders={data.reminders}
            tone={tone as ToneStyle}
            onCreateReminder={() => openModal('reminder')}
            onEditReminder={(id) => openModal('reminder', { entityId: id })}
            onCancelReminder={(id) => openModal('reminder-cancel', { entityId: id })}
          />
        );
      case 'personal':
        return (
          <PersonalDetail
            entries={data.personalEntries}
            categories={data.personalCategories ?? []}
            tone={tone as ToneStyle}
            onCreateCategory={() => openModal('personal-category')}
            onEditCategory={(id) => openModal('personal-category', { entityId: id })}
            onDeleteCategory={(id) => openModal('personal-delete-category', { entityId: id })}
            onCreateEntry={() => openModal('personal-entry')}
            onEditEntry={(id) => openModal('personal-entry', { entityId: id })}
            onDeleteEntry={(id) => openModal('personal-delete-entry', { entityId: id })}
          />
        );
      default:
        return <EmptyState title="Раздел в разработке" description="Выбери другой раздел." />;
    }
  };

  if (pin.enabled && pin.locked) {
    return <PinLock onUnlock={handleUnlock} onReset={handleResetPin} />;
  }

  if (isLoading) {
    return <Loader />;
  }

  if (error) {
    return (
      <AppLayout>
        <EmptyState
          title="Не удалось загрузить данные"
          description="Проверь подключение и попробуй снова."
          action={
            <Button onClick={() => refetch()}>
              Повторить
            </Button>
          }
        />
      </AppLayout>
    );
  }

  return (
    <AppLayout
      header={
        <Toolbar
          greeting={greeting}
          tone={tone as ToneStyle}
          onToneChange={(value) => setTone(value)}
          actions={
            <>
              <Button variant="secondary" onClick={() => refetch()}>
                Обновить данные
              </Button>
              <Button variant="secondary" onClick={() => setView('summary')}>
                К сводке
              </Button>
            </>
          }
        />
      }
    >
      {view === 'summary' && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {summaryCards.map((card) => (
            <SummaryCard
              key={card.key}
              icon={card.icon}
              title={card.title}
              primary={card.primary}
              secondary={card.secondary}
              action={
                <Button variant="ghost" onClick={() => {
                  setSection(card.key as typeof section);
                  setView('detail');
                }}>
                  Открыть
                </Button>
              }
            />
          ))}
        </div>
      )}

      {view === 'detail' && (
        <div className="space-y-4">
          <SectionHeader
            title={{
              analytics: 'Аналитика',
              tasks: 'Задачи',
              notes: 'Заметки',
              finances: 'Финансы',
              debts: 'Долги',
              reminders: 'Напоминания',
              personal: 'Личные записи',
            }[section] ?? 'Раздел'}
            subtitle="Детальная информация"
            onBack={() => setView('summary')}
          />
          {renderDetail()}
        </div>
      )}

      {renderModal()}
    </AppLayout>
  );
};

export default DashboardPage;
