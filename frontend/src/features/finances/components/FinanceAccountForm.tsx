import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { FinanceAccount } from '../../../api/types';
import Button from '../../../components/Button';

export type FinanceAccountFormValues = {
  name: string;
  balance: number;
  currency: string;
  institution?: string;
};

interface FinanceAccountFormProps {
  defaultValues?: Partial<FinanceAccount>;
  onSubmit: (values: FinanceAccountFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const FinanceAccountForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: FinanceAccountFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FinanceAccountFormValues>({
    defaultValues: {
      name: defaultValues?.name ?? '',
      balance: defaultValues?.balance ?? 0,
      currency: defaultValues?.currency ?? 'RUB',
      institution: defaultValues?.institution ?? '',
    },
  });

  useEffect(() => {
    reset({
      name: defaultValues?.name ?? '',
      balance: defaultValues?.balance ?? 0,
      currency: defaultValues?.currency ?? 'RUB',
      institution: defaultValues?.institution ?? '',
    });
  }, [defaultValues, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit(values);
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Название счёта</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('name', { required: 'Название обязательно' })}
        />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Баланс</span>
        <input
          type="number"
          step="0.01"
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('balance', { required: true, valueAsNumber: true })}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Валюта</span>
        <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('currency', { required: true })} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Банк / источник</span>
        <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('institution')} />
      </label>

      <div className="mt-4 flex justify-end gap-3">
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

export default FinanceAccountForm;
