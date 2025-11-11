import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import Button from '../../components/Button';
import type { PersonalCategory, PersonalEntry } from '../../api/types';

export type PersonalEntryFormInputs = {
  category_id?: string | null;
  title: string;
  data_type: PersonalEntry['data_type'];
  login_username?: string | null;
  login_password?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  document_number?: string | null;
  document_expiry?: string | null;
  custom_fields?: string;
  tags?: string;
  notes?: string | null;
  is_favorite?: boolean;
};

export type PersonalEntrySubmitValues = {
  category_id?: string | null;
  title: string;
  data_type: PersonalEntry['data_type'];
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
};

interface PersonalEntryFormProps {
  defaultValues?: PersonalEntry;
  categories: PersonalCategory[];
  onSubmit: (values: PersonalEntrySubmitValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const PersonalEntryForm = ({ defaultValues, categories, onSubmit, onCancel, submitLabel = 'Сохранить' }: PersonalEntryFormProps) => {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PersonalEntryFormInputs>({
    defaultValues: {
      category_id: defaultValues?.category_id ?? null,
      title: defaultValues?.title ?? '',
      data_type: defaultValues?.data_type ?? 'other',
      login_username: defaultValues?.login_username ?? '',
      login_password: defaultValues?.login_password ?? '',
      contact_name: defaultValues?.contact_name ?? '',
      contact_phone: defaultValues?.contact_phone ?? '',
      contact_email: defaultValues?.contact_email ?? '',
      document_number: defaultValues?.document_number ?? '',
      document_expiry: defaultValues?.document_expiry ?? '',
      custom_fields: defaultValues?.custom_fields ? JSON.stringify(defaultValues.custom_fields, null, 2) : '',
      tags: defaultValues?.tags?.join(', ') ?? '',
      notes: defaultValues?.notes ?? '',
      is_favorite: defaultValues?.is_favorite ?? false,
    },
  });

  const dataType = watch('data_type');

  useEffect(() => {
    reset({
      category_id: defaultValues?.category_id ?? null,
      title: defaultValues?.title ?? '',
      data_type: defaultValues?.data_type ?? 'other',
      login_username: defaultValues?.login_username ?? '',
      login_password: defaultValues?.login_password ?? '',
      contact_name: defaultValues?.contact_name ?? '',
      contact_phone: defaultValues?.contact_phone ?? '',
      contact_email: defaultValues?.contact_email ?? '',
      document_number: defaultValues?.document_number ?? '',
      document_expiry: defaultValues?.document_expiry ?? '',
      custom_fields: defaultValues?.custom_fields ? JSON.stringify(defaultValues.custom_fields, null, 2) : '',
      tags: defaultValues?.tags?.join(', ') ?? '',
      notes: defaultValues?.notes ?? '',
      is_favorite: defaultValues?.is_favorite ?? false,
    });
  }, [defaultValues, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        let parsedCustomFields: Record<string, unknown> | null = null;
        if (values.custom_fields) {
          try {
            parsedCustomFields = JSON.parse(values.custom_fields);
          } catch (error) {
            setError('custom_fields', { type: 'manual', message: 'Введите корректный JSON' });
            return;
          }
        }
        const tagsArray = values.tags
          ? values.tags
              .split(',')
              .map((tag) => tag.trim())
              .filter(Boolean)
          : null;
        await onSubmit({
          ...values,
          category_id: values.category_id || null,
          custom_fields: parsedCustomFields,
          tags: tagsArray,
        });
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Название</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('title', { required: 'Название обязательно' })}
        />
        {errors.title && <span className="text-xs text-danger">{errors.title.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Категория</span>
        <select className="rounded-md border border-border bg-surface px-3 py-2" {...register('category_id')}> 
          <option value="">Без категории</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Тип данных</span>
        <select className="rounded-md border border-border bg-surface px-3 py-2" {...register('data_type')}>
          <option value="login">Доступ</option>
          <option value="contact">Контакт</option>
          <option value="document">Документ</option>
          <option value="other">Другое</option>
        </select>
      </label>

      {dataType === 'login' && (
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            <span>Логин</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('login_username')} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span>Пароль</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('login_password')} />
          </label>
        </div>
      )}

      {dataType === 'contact' && (
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            <span>Имя</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('contact_name')} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span>Телефон</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('contact_phone')} />
          </label>
          <label className="flex flex-col gap-1 text-sm md:col-span-2">
            <span>Email</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('contact_email')} />
          </label>
        </div>
      )}

      {dataType === 'document' && (
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm md:col-span-2">
            <span>Номер документа</span>
            <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('document_number')} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span>Дата окончания</span>
            <input type="date" className="rounded-md border border-border bg-surface px-3 py-2" {...register('document_expiry')} />
          </label>
        </div>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span>Настраиваемые поля (JSON)</span>
        <textarea className="rounded-md border border-border bg-surface px-3 py-2" rows={3} {...register('custom_fields')} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Теги (через запятую)</span>
        <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('tags')} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Заметки</span>
        <textarea className="rounded-md border border-border bg-surface px-3 py-2" rows={3} {...register('notes')} />
      </label>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="h-4 w-4" {...register('is_favorite')} />
        <span>Добавить в избранное</span>
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

export default PersonalEntryForm;
