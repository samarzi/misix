import axios from 'axios';
import type {
  DashboardSummaryResponse,
  TaskSummary,
  NoteSummary,
  FinanceAccount,
  FinanceCategory,
  FinanceRule,
  FinanceTransaction,
  ReminderSummary,
  PersonalCategory,
  PersonalEntry,
} from './types';
import { API_BASE_URL } from '../config';

export type CreateTransactionPayload = Omit<FinanceTransaction, 'id' | 'occurred_at'> & {
  occurred_at?: string;
};

export type UpdateTransactionPayload = Partial<CreateTransactionPayload> & { id: string };

export type CreateAccountPayload = Omit<FinanceAccount, 'id'>;

export type UpdateAccountPayload = Partial<CreateAccountPayload> & { id: string };

export type CreateCategoryPayload = Omit<FinanceCategory, 'id'>;

export type UpdateCategoryPayload = Partial<CreateCategoryPayload> & { id: string };

export type CreateRulePayload = Omit<FinanceRule, 'id'>;

export type UpdateRulePayload = Partial<CreateRulePayload> & { id: string };

export type CreateReminderPayload = {
  title: string;
  reminder_time: string;
  timezone: string;
  status?: ReminderSummary['status'];
  recurrence_rule?: string | null;
  payload?: Record<string, unknown> | null;
};

export type UpdateReminderPayload = {
  id: string;
  title?: string;
  reminder_time?: string;
  timezone?: string;
  status?: ReminderSummary['status'];
  recurrence_rule?: string | null;
  payload?: Record<string, unknown> | null;
};

export type CreatePersonalCategoryPayload = Omit<PersonalCategory, 'id'>;

export type UpdatePersonalCategoryPayload = Partial<CreatePersonalCategoryPayload> & { id: string };

export type CreatePersonalEntryPayload = Omit<PersonalEntry, 'id' | 'is_confidential'>;

export type UpdatePersonalEntryPayload = Partial<CreatePersonalEntryPayload> & { id: string };

export type CreateTaskPayload = {
  title: string;
  description?: string | null;
  priority?: TaskSummary['priority'];
  status?: TaskSummary['status'];
  deadline?: string | null;
  estimated_hours?: number | null;
  actual_hours?: number | null;
  project_id?: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & { id: string };

export type CreateNotePayload = {
  title?: string | null;
  content: string;
  content_format?: string;
  folder_id?: string | null;
};

export type UpdateNotePayload = Partial<CreateNotePayload> & { id: string };

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API error', error.response.status, error.response.data);
    } else {
      console.error('Network error', error);
    }
    return Promise.reject(error);
  },
);

export const fetchDashboardSummary = async (userId: string) => {
  const params = new URLSearchParams({
    user_id: userId,
  });
  const { data } = await client.get<DashboardSummaryResponse>(`/api/dashboard/summary?${params.toString()}`);
  return data;
};

export const createTransaction = async (payload: CreateTransactionPayload) => {
  const { data } = await client.post<FinanceTransaction>('/api/finances/transactions', payload);
  return data;
};

export const updateTransaction = async (payload: UpdateTransactionPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<FinanceTransaction>(`/api/finances/transactions/${id}`, rest);
  return data;
};

export const deleteTransaction = async (id: string) => {
  await client.delete(`/api/finances/transactions/${id}`);
};

export const createAccount = async (payload: CreateAccountPayload) => {
  const { data } = await client.post<FinanceAccount>('/api/finances/accounts', payload);
  return data;
};

export const updateAccount = async (payload: UpdateAccountPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<FinanceAccount>(`/api/finances/accounts/${id}`, rest);
  return data;
};

export const deleteAccount = async (id: string) => {
  await client.delete(`/api/finances/accounts/${id}`);
};

export const createCategory = async (payload: CreateCategoryPayload) => {
  const { data } = await client.post<FinanceCategory>('/api/finances/categories', payload);
  return data;
};

export const updateCategory = async (payload: UpdateCategoryPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<FinanceCategory>(`/api/finances/categories/${id}`, rest);
  return data;
};

export const deleteCategory = async (id: string) => {
  await client.delete(`/api/finances/categories/${id}`);
};

export const createRule = async (payload: CreateRulePayload) => {
  const { data } = await client.post<FinanceRule>('/api/finances/rules', payload);
  return data;
};

export const updateRule = async (payload: UpdateRulePayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<FinanceRule>(`/api/finances/rules/${id}`, rest);
  return data;
};

export const deleteRule = async (id: string) => {
  await client.delete(`/api/finances/rules/${id}`);
};

export const createReminder = async (payload: CreateReminderPayload) => {
  const { data } = await client.post<ReminderSummary>('/api/finances/reminders', payload);
  return data;
};

export const updateReminder = async (payload: UpdateReminderPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<ReminderSummary>(`/api/finances/reminders/${id}`, rest);
  return data;
};

export const cancelReminder = async (id: string) => {
  await client.post(`/api/finances/reminders/${id}/cancel`);
};

export const createPersonalCategory = async (payload: CreatePersonalCategoryPayload) => {
  const { data } = await client.post<PersonalCategory>('/api/personal/categories', payload);
  return data;
};

export const updatePersonalCategory = async (payload: UpdatePersonalCategoryPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<PersonalCategory>(`/api/personal/categories/${id}`, rest);
  return data;
};

export const deletePersonalCategory = async (id: string) => {
  await client.delete(`/api/personal/categories/${id}`);
};

export const createPersonalEntry = async (payload: CreatePersonalEntryPayload) => {
  const { data } = await client.post<PersonalEntry>('/api/personal/entries', payload);
  return data;
};

export const updatePersonalEntry = async (payload: UpdatePersonalEntryPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<PersonalEntry>(`/api/personal/entries/${id}`, rest);
  return data;
};

export const deletePersonalEntry = async (id: string) => {
  await client.delete(`/api/personal/entries/${id}`);
};

export const createTask = async (payload: CreateTaskPayload) => {
  const { data } = await client.post<TaskSummary>('/api/tasks', payload);
  return data;
};

export const updateTask = async (payload: UpdateTaskPayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<TaskSummary>(`/api/tasks/${id}`, rest);
  return data;
};

export const deleteTask = async (id: string) => {
  await client.delete(`/api/tasks/${id}`);
};

export const createNote = async (payload: CreateNotePayload) => {
  const { data } = await client.post<NoteSummary>('/api/notes', payload);
  return data;
};

export const updateNote = async (payload: UpdateNotePayload) => {
  const { id, ...rest } = payload;
  const { data } = await client.put<NoteSummary>(`/api/notes/${id}`, rest);
  return data;
};

export const deleteNote = async (id: string) => {
  await client.delete(`/api/notes/${id}`);
};
