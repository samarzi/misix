import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import Button from '../../components/Button';
import type { ReminderSummary } from '../../api/types';

export type ReminderFormValues = {
  title: string;
  reminder_time: string;
  timezone: string;
  status: ReminderSummary['status'];
  recurrence_rule?: string | null;
};

interface ReminderFormProps {
  defaultValues?: ReminderSummary;
  onSubmit: (values: ReminderFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const toLocalInputValue = (isoString?: string) => {
  if (!isoString) return new Date().toISOString().slice(0, 16);
  const date = new Date(isoString);
  const tzOffset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - tzOffset * 60 * 1000);
  return local.toISOString().slice(0, 16);
};

const ReminderForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: ReminderFormProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ReminderFormValues>({
    defaultValues: {
      title: defaultValues?.title ?? '',
      reminder_time: toLocalInputValue(defaultValues?.reminder_time),
      timezone: defaultValues?.timezone ?? 'Europe/Moscow',
      status: defaultValues?.status ?? 'scheduled',
      recurrence_rule: defaultValues?.recurrence_rule ?? null,
    },
  });

  useEffect(() => {
    reset({
      title: defaultValues?.title ?? '',
      reminder_time: toLocalInputValue(defaultValues?.reminder_time),
      timezone: defaultValues?.timezone ?? 'Europe/Moscow',
      status: defaultValues?.status ?? 'scheduled',
      recurrence_rule: defaultValues?.recurrence_rule ?? null,
    });
  }, [defaultValues, reset]);

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={handleSubmit(async (values) => {
        const isoTime = new Date(values.reminder_time).toISOString();
        await onSubmit({
          ...values,
          reminder_time: isoTime,
          recurrence_rule: values.recurrence_rule?.trim() ? values.recurrence_rule : null,
        });
      })}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span>Заголовок</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('title', { required: 'Название обязательно' })}
        />
        {errors.title && <span className="text-xs text-danger">{errors.title.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Дата и время</span>
        <input
          type="datetime-local"
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('reminder_time', { required: 'Укажи время' })}
        />
        {errors.reminder_time && <span className="text-xs text-danger">{errors.reminder_time.message}</span>}
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Часовой пояс</span>
        <input
          className="rounded-md border border-border bg-surface px-3 py-2"
          {...register('timezone', { required: 'Укажи часовой пояс' })}
        />
        <span className="text-xs text-textMuted">Например: Europe/Moscow</span>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Статус</span>
        <select className="rounded-md border border-border bg-surface px-3 py-2" {...register('status')}>
          <option value="scheduled">Запланировано</option>
          <option value="done">Выполнено</option>
          <option value="cancelled">Отменено</option>
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>Правило повторения (RRULE)</span>
        <input className="rounded-md border border-border bg-surface px-3 py-2" {...register('recurrence_rule')} />
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

export default ReminderForm;
