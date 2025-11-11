import type { TaskPriority, TaskStatus, TaskSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';

interface TasksDetailProps {
  tasks: TaskSummary[];
  tone: ToneStyle;
  onCreate: () => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  statusFilter: TaskStatus | 'all';
  priorityFilter: TaskPriority | 'all';
  onStatusFilterChange: (value: TaskStatus | 'all') => void;
  onPriorityFilterChange: (value: TaskPriority | 'all') => void;
}

const statusLabel: Record<TaskSummary['status'], string> = {
  new: 'Новая',
  in_progress: 'В работе',
  waiting: 'Ожидает',
  completed: 'Выполнена',
  cancelled: 'Отменена',
};

const priorityLabel: Record<TaskPriority, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  critical: 'Критичный',
};

const TasksDetail = ({
  tasks,
  tone,
  onCreate,
  onEdit,
  onDelete,
  statusFilter,
  priorityFilter,
  onStatusFilterChange,
  onPriorityFilterChange,
}: TasksDetailProps) => {
  if (!tasks.length) {
    const empty = getEmptyStateMessage(tone, 'Задачи');
    return <EmptyState title={empty.title} description={empty.description} action={<Button onClick={onCreate}>Добавить задачу</Button>} />;
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <Button variant="secondary" onClick={onCreate}>
          Новая задача
        </Button>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-textMuted">
            Статус
            <select
              className="rounded-full border border-borderStrong bg-surfaceGlass px-3 py-1 text-sm text-text focus:border-primary focus:outline-none"
              value={statusFilter}
              onChange={(event) => onStatusFilterChange(event.target.value as TaskStatus | 'all')}
            >
              <option value="all">Все</option>
              {Object.entries(statusLabel).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-textMuted">
            Приоритет
            <select
              className="rounded-full border border-borderStrong bg-surfaceGlass px-3 py-1 text-sm text-text focus:border-primary focus:outline-none"
              value={priorityFilter}
              onChange={(event) => onPriorityFilterChange(event.target.value as TaskPriority | 'all')}
            >
              <option value="all">Все</option>
              {Object.entries(priorityLabel).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
      {tasks.map((task) => (
        <div key={task.id} className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-text">{task.title}</h3>
              {task.description && <p className="mt-1 text-sm text-textSecondary">{task.description}</p>}
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-textMuted">
                <span className="rounded-full border border-borderStrong bg-surfaceGlass px-3 py-1 font-semibold">
                  {statusLabel[task.status]}
                </span>
                {task.priority && (
                  <span className="rounded-full border border-primary bg-primaryMuted/30 px-3 py-1 font-semibold text-primary">
                    {priorityLabel[task.priority]}
                  </span>
                )}
                {task.deadline && (
                  <span className="rounded-full border border-borderStrong bg-surfaceGlass px-3 py-1">
                    Срок: {new Date(task.deadline).toLocaleString('ru-RU')}
                  </span>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" onClick={() => onEdit(task.id)}>
                ✏️
              </Button>
              <Button variant="ghost" className="text-danger" onClick={() => onDelete(task.id)}>
                Удалить
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TasksDetail;
