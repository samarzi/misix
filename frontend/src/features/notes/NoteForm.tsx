import { useForm } from 'react-hook-form';
import Button from '../../components/Button';
import type { NoteSummary } from '../../api/types';

export interface NoteFormValues {
  title?: string | null;
  content: string;
  content_format?: string;
}

interface NoteFormProps {
  defaultValues?: NoteSummary;
  onSubmit: (values: NoteFormValues) => Promise<void> | void;
  onCancel: () => void;
  submitLabel?: string;
}

const NoteForm = ({ defaultValues, onSubmit, onCancel, submitLabel = 'Сохранить' }: NoteFormProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<NoteFormValues>({
    defaultValues: {
      title: defaultValues?.title ?? '',
      content: defaultValues?.content ?? '',
      content_format: defaultValues?.content_format ?? 'markdown',
    },
  });

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit(values);
      })}
    >
      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Заголовок</span>
        <input
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          placeholder="Например: Идея проекта"
          {...register('title')}
        />
      </label>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Содержимое</span>
        <textarea
          className="min-h-[200px] rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          placeholder="Напиши заметку..."
          {...register('content', { required: 'Содержимое обязательно' })}
        />
        {errors.content && <span className="text-xs text-danger">{errors.content.message}</span>}
      </label>

      <label className="flex flex-col gap-2 text-sm text-textMuted">
        <span className="text-xs uppercase tracking-[0.2em] text-textMuted">Формат</span>
        <select
          className="rounded-xl border border-borderStrong bg-surface/60 px-4 py-2 text-text transition-colors focus:border-primary focus:outline-none"
          {...register('content_format')}
        >
          <option value="markdown">Markdown</option>
          <option value="text">Plain text</option>
        </select>
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

export default NoteForm;
