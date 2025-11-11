import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { FinanceCategory } from '../../../api/types';
import Button from '../../../components/Button';

export type FinanceCategoryFormValues = {
  name: string;
  budget?: number | null;
};

interface FinanceCategoryFormProps {
  defaultValues?: Partial<FinanceCategory>;
  onSubmit: (values: FinanceCategoryFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const FinanceCategoryForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: FinanceCategoryFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FinanceCategoryFormValues>({
    defaultValues: {
      name: defaultValues?.name ?? '',
      budget: defaultValues?.budget ?? undefined,
    },
  });

  useEffect(() => {
    reset({
      name: defaultValues?.name ?? '',
      budget: defaultValues?.budget ?? undefined,
    });
  }, [defaultValues, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          ...values,
          budget: values.budget === undefined || values.budget === null ? undefined : Number(values.budget),
        });
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Название категории</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('name', { required: 'Название обязательно' })}
        />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Бюджет (опционально)</span>
        <input
          type="number"
          step="0.01"
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('budget', { valueAsNumber: true })}
        />
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

export default FinanceCategoryForm;
