import type { ReminderSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';
import { formatDateTime } from '../../utils/format';

interface RemindersDetailProps {
  reminders: ReminderSummary[];
  tone: ToneStyle;
  onCreateReminder: () => void;
  onEditReminder: (id: string) => void;
  onCancelReminder: (id: string) => void;
}

const statusLabel: Record<ReminderSummary['status'], string> = {
  scheduled: 'Запланировано',
  done: 'Выполнено',
  cancelled: 'Отменено',
};

const statusBadgeClass: Record<ReminderSummary['status'], string> = {
  scheduled: 'border-primary text-primary',
  done: 'border-success text-success',
  cancelled: 'border-border text-textMuted',
};

const RemindersDetail = ({ reminders, tone, onCreateReminder, onEditReminder, onCancelReminder }: RemindersDetailProps) => {
  if (!reminders.length) {
    const empty = getEmptyStateMessage(tone, 'Напоминания');
    return (
      <EmptyState
        title={empty.title}
        description={empty.description}
        action={
          <Button onClick={onCreateReminder}>
            Добавить напоминание
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="secondary" onClick={onCreateReminder}>
          Новое напоминание
        </Button>
      </div>
      {reminders.map((reminder) => (
        <div
          key={reminder.id}
          className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-300 ease-out-soft hover:-translate-y-1 hover:shadow-glow"
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Напоминание</p>
              <h3 className="text-lg font-semibold text-text">{reminder.title}</h3>
              <p className="text-sm text-textSecondary">{formatDateTime(reminder.reminder_time)}</p>
              <p className="text-xs text-textMuted">Часовой пояс: {reminder.timezone}</p>
              {reminder.recurrence_rule && (
                <p className="text-xs text-textMuted">Повторение: {reminder.recurrence_rule}</p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusBadgeClass[reminder.status]}`}>
                {statusLabel[reminder.status]}
              </span>
              <Button variant="ghost" onClick={() => onEditReminder(reminder.id)}>
                ✏️
              </Button>
              {reminder.status === 'scheduled' && (
                <Button variant="ghost" className="text-danger" onClick={() => onCancelReminder(reminder.id)}>
                  Отменить
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RemindersDetail;
