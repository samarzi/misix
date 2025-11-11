import { useForm } from 'react-hook-form';
import Button from '../../components/Button';
import type { TaskPriority, TaskStatus, TaskSummary } from '../../api/types';

export interface TaskFormValues {
  title: string;
  description?: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  deadline?: string | null;
}

interface TaskFormProps {
  defaultValues?: TaskSummary;
  onSubmit: (values: TaskFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const priorityOptions: TaskPriority[] = ['low', 'medium', 'high', 'critical'];
const statusOptions: TaskStatus[] = ['new', 'in_progress', 'waiting', 'completed', 'cancelled'];

const TaskForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: TaskFormProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormValues>({
    defaultValues: {
      title: defaultValues?.title ?? '',
      description: defaultValues?.description ?? '',
      priority: defaultValues?.priority ?? 'medium',
      status: defaultValues?.status ?? 'new',
      deadline: defaultValues?.deadline ? defaultValues.deadline.slice(0, 16) : '',
    },
  });

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          ...values,
          deadline: values.deadline ? new Date(values.deadline).toISOString() : null,
        });
      })}
    >
      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Название</span>
        <input
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          placeholder="Например: Подготовить отчёт"
          {...register('title', { required: 'Укажи название задачи' })}
        />
        {errors.title && <span className="text-xs text-danger">{errors.title.message}</span>}
      </label>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Описание</span>
        <textarea
          className="h-28 rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          placeholder="Добавь детали задачи"
          {...register('description')}
        />
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm text-textMuted">
          <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Приоритет</span>
          <select
            className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
            {...register('priority')}
          >
            {priorityOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-textMuted">
          <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Статус</span>
          <select
            className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
            {...register('status')}
          >
            {statusOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Дедлайн</span>
        <input
          type="datetime-local"
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          {...register('deadline')}
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

export default TaskForm;
