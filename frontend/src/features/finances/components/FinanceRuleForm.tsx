import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { FinanceCategory, FinanceRule } from '../../../api/types';
import Button from '../../../components/Button';

export type FinanceRuleFormValues = {
  name: string;
  description?: string;
  is_active: boolean;
  category_id?: string;
};

type RuleDefaultValues = Partial<FinanceRule> & { category_id?: string | null };

interface FinanceRuleFormProps {
  defaultValues?: RuleDefaultValues;
  categories: FinanceCategory[];
  onSubmit: (values: FinanceRuleFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const FinanceRuleForm = ({ defaultValues, categories, onSubmit, onCancel, submitLabel = 'Сохранить' }: FinanceRuleFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FinanceRuleFormValues>({
    defaultValues: {
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
      is_active: defaultValues?.is_active ?? true,
      category_id: defaultValues?.category_id ?? categories[0]?.id,
    },
  });

  useEffect(() => {
    reset({
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
      is_active: defaultValues?.is_active ?? true,
      category_id: defaultValues?.category_id ?? categories[0]?.id,
    });
  }, [defaultValues, categories, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit(values);
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Название</span>
        <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('name', { required: 'Название обязательно' })} />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Описание</span>
        <textarea className="rounded-md border border-border bg-surface px-3 py-2" rows={3} {...register('description')} />
      </label>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="h-4 w-4" {...register('is_active')} />
        <span>Правило активно</span>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Категория (опционально)</span>
        <select className="rounded-md border border-border bg-surface px-3 py-2" {...register('category_id')}>
          <option value="">Не выбрана</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
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

export default FinanceRuleForm;
