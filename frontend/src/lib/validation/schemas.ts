/**
 * Zod validation schemas for frontend forms
 * 
 * These schemas provide client-side validation before sending data to the API.
 * They mirror the backend Pydantic models to ensure consistency.
 */

import { z } from 'zod';

// ============================================================================
// Authentication Schemas
// ============================================================================

/**
 * Password validation regex
 * - At least 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 * - At least one special character
 */
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])/;

export const registerSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email format'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must not exceed 100 characters')
    .regex(passwordRegex, 'Password must contain uppercase, lowercase, digit, and special character'),
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(200, 'Full name must not exceed 200 characters')
    .trim(),
  telegram_id: z.number().int().positive().optional(),
});

export type RegisterInput = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email format'),
  password: z
    .string()
    .min(1, 'Password is required'),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const changePasswordSchema = z.object({
  current_password: z
    .string()
    .min(1, 'Current password is required'),
  new_password: z
    .string()
    .min(8, 'New password must be at least 8 characters')
    .max(100, 'New password must not exceed 100 characters')
    .regex(passwordRegex, 'Password must contain uppercase, lowercase, digit, and special character'),
}).refine((data) => data.current_password !== data.new_password, {
  message: 'New password must be different from current password',
  path: ['new_password'],
});

export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;

// ============================================================================
// Task Schemas
// ============================================================================

export const taskStatusEnum = z.enum([
  'new',
  'in_progress',
  'waiting',
  'completed',
  'cancelled',
]);

export const taskPriorityEnum = z.enum([
  'low',
  'medium',
  'high',
  'critical',
]);

export const createTaskSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(500, 'Title must not exceed 500 characters')
    .trim(),
  description: z
    .string()
    .max(5000, 'Description must not exceed 5000 characters')
    .optional()
    .nullable(),
  priority: taskPriorityEnum.default('medium'),
  status: taskStatusEnum.default('new'),
  deadline: z
    .date()
    .min(new Date(), 'Deadline cannot be in the past')
    .optional()
    .nullable(),
  estimated_hours: z
    .number()
    .min(0, 'Estimated hours must be positive')
    .max(1000, 'Estimated hours must not exceed 1000')
    .optional()
    .nullable(),
  actual_hours: z
    .number()
    .min(0, 'Actual hours must be positive')
    .max(1000, 'Actual hours must not exceed 1000')
    .optional()
    .nullable(),
  project_id: z.string().uuid().optional().nullable(),
});

export type CreateTaskInput = z.infer<typeof createTaskSchema>;

export const updateTaskSchema = createTaskSchema.partial();

export type UpdateTaskInput = z.infer<typeof updateTaskSchema>;

// ============================================================================
// Note Schemas
// ============================================================================

export const noteContentFormatEnum = z.enum(['markdown', 'html', 'plain']);

export const createNoteSchema = z.object({
  title: z
    .string()
    .max(500, 'Title must not exceed 500 characters')
    .trim()
    .optional()
    .nullable(),
  content: z
    .string()
    .min(1, 'Content is required')
    .max(100000, 'Content must not exceed 100000 characters')
    .trim(),
  content_format: noteContentFormatEnum.default('markdown'),
  folder_id: z.string().uuid().optional().nullable(),
  is_favorite: z.boolean().default(false),
});

export type CreateNoteInput = z.infer<typeof createNoteSchema>;

export const updateNoteSchema = z.object({
  title: z
    .string()
    .max(500, 'Title must not exceed 500 characters')
    .trim()
    .optional()
    .nullable(),
  content: z
    .string()
    .min(1, 'Content is required')
    .max(100000, 'Content must not exceed 100000 characters')
    .trim()
    .optional(),
  content_format: noteContentFormatEnum.optional(),
  folder_id: z.string().uuid().optional().nullable(),
  is_favorite: z.boolean().optional(),
  is_archived: z.boolean().optional(),
});

export type UpdateNoteInput = z.infer<typeof updateNoteSchema>;

// ============================================================================
// Finance Schemas
// ============================================================================

export const transactionTypeEnum = z.enum(['income', 'expense']);

export const createTransactionSchema = z.object({
  amount: z
    .number()
    .refine((val) => val !== 0, 'Amount cannot be zero')
    .refine((val) => Number.isFinite(val), 'Amount must be a valid number'),
  currency: z
    .string()
    .length(3, 'Currency code must be 3 characters')
    .toUpperCase()
    .default('RUB'),
  type: transactionTypeEnum,
  category_id: z.string().uuid().optional().nullable(),
  account_id: z.string().uuid().optional().nullable(),
  description: z
    .string()
    .max(500, 'Description must not exceed 500 characters')
    .optional()
    .nullable(),
  merchant: z
    .string()
    .max(200, 'Merchant name must not exceed 200 characters')
    .optional()
    .nullable(),
  transaction_date: z.date().default(() => new Date()),
  notes: z
    .string()
    .max(1000, 'Notes must not exceed 1000 characters')
    .optional()
    .nullable(),
});

export type CreateTransactionInput = z.infer<typeof createTransactionSchema>;

export const updateTransactionSchema = createTransactionSchema.partial();

export type UpdateTransactionInput = z.infer<typeof updateTransactionSchema>;

export const createCategorySchema = z.object({
  name: z
    .string()
    .min(1, 'Category name is required')
    .max(100, 'Category name must not exceed 100 characters')
    .trim(),
  type: transactionTypeEnum,
  budget: z
    .number()
    .min(0, 'Budget must be positive')
    .optional()
    .nullable(),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, 'Color must be a valid hex code')
    .optional()
    .nullable(),
  icon: z
    .string()
    .max(10, 'Icon must not exceed 10 characters')
    .optional()
    .nullable(),
});

export type CreateCategoryInput = z.infer<typeof createCategorySchema>;

export const updateCategorySchema = z.object({
  name: z
    .string()
    .min(1, 'Category name is required')
    .max(100, 'Category name must not exceed 100 characters')
    .trim()
    .optional(),
  budget: z
    .number()
    .min(0, 'Budget must be positive')
    .optional()
    .nullable(),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, 'Color must be a valid hex code')
    .optional()
    .nullable(),
  icon: z
    .string()
    .max(10, 'Icon must not exceed 10 characters')
    .optional()
    .nullable(),
});

export type UpdateCategoryInput = z.infer<typeof updateCategorySchema>;

export const createAccountSchema = z.object({
  name: z
    .string()
    .min(1, 'Account name is required')
    .max(200, 'Account name must not exceed 200 characters')
    .trim(),
  balance: z
    .number()
    .default(0),
  currency: z
    .string()
    .length(3, 'Currency code must be 3 characters')
    .toUpperCase()
    .default('RUB'),
  institution: z
    .string()
    .max(200, 'Institution name must not exceed 200 characters')
    .optional()
    .nullable(),
});

export type CreateAccountInput = z.infer<typeof createAccountSchema>;

export const updateAccountSchema = createAccountSchema.partial();

export type UpdateAccountInput = z.infer<typeof updateAccountSchema>;

// ============================================================================
// File Upload Schemas
// ============================================================================

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

export const fileUploadSchema = z.object({
  file: z
    .instanceof(File)
    .refine((file) => file.size <= MAX_FILE_SIZE, 'File size must not exceed 10MB')
    .refine(
      (file) => ALLOWED_FILE_TYPES.includes(file.type),
      'File type not allowed. Allowed types: images, PDF, text, Word documents'
    ),
});

export type FileUploadInput = z.infer<typeof fileUploadSchema>;

// ============================================================================
// Common Schemas
// ============================================================================

export const paginationSchema = z.object({
  page: z
    .number()
    .int()
    .min(1, 'Page must be at least 1')
    .default(1),
  page_size: z
    .number()
    .int()
    .min(1, 'Page size must be at least 1')
    .max(100, 'Page size must not exceed 100')
    .default(20),
});

export type PaginationInput = z.infer<typeof paginationSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validate data against a schema and return formatted errors
 */
export function validateSchema<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; errors: Record<string, string[]> } {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  // Format Zod errors into field-level errors
  const errors: Record<string, string[]> = {};
  
  result.error.issues.forEach((error: z.ZodIssue) => {
    const path = error.path.join('.');
    if (!errors[path]) {
      errors[path] = [];
    }
    errors[path].push(error.message);
  });

  return { success: false, errors };
}

/**
 * Get first error message for a field
 */
export function getFieldError(
  errors: Record<string, string[]> | undefined,
  field: string
): string | undefined {
  return errors?.[field]?.[0];
}

/**
 * Check if a field has errors
 */
export function hasFieldError(
  errors: Record<string, string[]> | undefined,
  field: string
): boolean {
  return Boolean(errors?.[field]?.length);
}

// ============================================================================
// Custom Validators
// ============================================================================

/**
 * Validate that a string doesn't contain HTML tags
 */
export const noHtmlTags = z.string().refine(
  (val) => !/<[^>]+>/.test(val),
  'HTML tags are not allowed'
);

/**
 * Validate URL format
 */
export const urlSchema = z.string().url('Invalid URL format');

/**
 * Validate phone number (basic international format)
 */
export const phoneSchema = z.string().regex(
  /^\+?[1-9]\d{1,14}$/,
  'Invalid phone number format'
);

/**
 * Validate hex color code
 */
export const hexColorSchema = z.string().regex(
  /^#[0-9A-Fa-f]{6}$/,
  'Invalid hex color code'
);

/**
 * Validate that a date is in the future
 */
export const futureDateSchema = z.date().refine(
  (date) => date > new Date(),
  'Date must be in the future'
);

/**
 * Validate that a date is in the past
 */
export const pastDateSchema = z.date().refine(
  (date) => date < new Date(),
  'Date must be in the past'
);
