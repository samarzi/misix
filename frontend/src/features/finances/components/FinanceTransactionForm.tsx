import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { FinanceAccount, FinanceCategory, FinanceTransaction } from '../../../api/types';
import Button from '../../../components/Button';

const resolveTransactionType = (amount?: number | null): 'income' | 'expense' => {
  if (amount == null) return 'expense';
  return amount >= 0 ? 'income' : 'expense';
};

export type FinanceTransactionFormValues = {
  amount: number;
  account_id: string;
  category_id: string;
  description?: string;
  occurred_at?: string;
  type: 'income' | 'expense';
};

interface FinanceTransactionFormProps {
  defaultValues?: Partial<FinanceTransaction>;
  accounts: FinanceAccount[];
  categories: FinanceCategory[];
  onSubmit: (values: FinanceTransactionFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const FinanceTransactionForm = ({
  defaultValues,
  accounts,
  categories,
  onSubmit,
  onCancel,
  submitLabel = 'Сохранить',
}: FinanceTransactionFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FinanceTransactionFormValues>({
    defaultValues: {
      amount: defaultValues?.amount ?? 0,
      account_id: defaultValues?.account_id ?? (accounts[0]?.id ?? ''),
      category_id: defaultValues?.category_id ?? (categories[0]?.id ?? ''),
      description: defaultValues?.description ?? '',
      occurred_at: defaultValues?.occurred_at?.slice(0, 16) ?? new Date().toISOString().slice(0, 16),
      type: resolveTransactionType(defaultValues?.amount ?? 0),
    },
  });

  useEffect(() => {
    reset({
      amount: defaultValues?.amount ?? 0,
      account_id: defaultValues?.account_id ?? (accounts[0]?.id ?? ''),
      category_id: defaultValues?.category_id ?? (categories[0]?.id ?? ''),
      description: defaultValues?.description ?? '',
      occurred_at: defaultValues?.occurred_at?.slice(0, 16) ?? new Date().toISOString().slice(0, 16),
      type: resolveTransactionType(defaultValues?.amount ?? 0),
    });
  }, [defaultValues, accounts, categories, reset]);

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit(values);
        reset();
      })}
    >
      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Сумма</span>
        <input
          type="number"
          step="0.01"
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
          {...register('amount', { required: 'Укажи сумму', valueAsNumber: true })}
        />
        {errors.amount && <span className="text-xs text-danger">{errors.amount.message}</span>}
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm text-textMuted">
          <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Счёт</span>
          <select
            className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
            {...register('account_id', { required: true })}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-textMuted">
          <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Категория</span>
          <select
            className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
            {...register('category_id', { required: true })}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Тип</span>
        <select
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          {...register('type')}
        >
          <option value="income">Доход</option>
          <option value="expense">Расход</option>
        </select>
      </label>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Описание</span>
        <input
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          placeholder="Например: Аренда офиса"
          {...register('description')}
        />
      </label>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Дата</span>
        <input
          type="datetime-local"
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          {...register('occurred_at')}
        />
      </label>

      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Отмена
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Сохраняю...' : submitLabel}
        </Button>
      </div>
    </form>
  );
};

export default FinanceTransactionForm;
