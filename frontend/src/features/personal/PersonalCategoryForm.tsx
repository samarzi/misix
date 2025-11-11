import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import Button from '../../components/Button';
import type { PersonalCategory } from '../../api/types';

export type PersonalCategoryFormValues = {
  name: string;
  description?: string | null;
  color?: string | null;
  icon?: string | null;
  is_confidential?: boolean;
};

interface PersonalCategoryFormProps {
  defaultValues?: PersonalCategory;
  onSubmit: (values: PersonalCategoryFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const PersonalCategoryForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: PersonalCategoryFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PersonalCategoryFormValues>({
    defaultValues: {
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
      color: defaultValues?.color ?? '',
      icon: defaultValues?.icon ?? '',
      is_confidential: defaultValues?.is_confidential ?? false,
    },
  });

  useEffect(() => {
    reset({
      name: defaultValues?.name ?? '',
      description: defaultValues?.description ?? '',
      color: defaultValues?.color ?? '',
      icon: defaultValues?.icon ?? '',
      is_confidential: defaultValues?.is_confidential ?? false,
    });
  }, [defaultValues, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          ...values,
          description: values.description?.trim() ? values.description : null,
          color: values.color?.trim() ? values.color : null,
          icon: values.icon?.trim() ? values.icon : null,
        });
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Название</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('name', { required: 'Название обязательно' })}
        />
        {errors.name && <span className="text-xs text-danger">{errors.name.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Описание</span>
        <textarea className="rounded-md border border-border bg-surface px-3 py-2" rows={3} {...register('description')} />
      </label>

      <div className="grid gap-3 md:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span>Цвет</span>
          <input className="rounded-md border border-border bg-surface px-3 py-2" placeholder="#cccccc" {...register('color')} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span>Иконка</span>
          <input className="rounded-md border border-border bg-surface px-3 py-2" placeholder="🔐" {...register('icon')} />
        </label>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="h-4 w-4" {...register('is_confidential')} />
        <span>Конфиденциальная категория</span>
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

export default PersonalCategoryForm;
