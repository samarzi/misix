import type { TaskSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';

interface TasksDetailProps {
  tasks: TaskSummary[];
  tone: ToneStyle;
}

const statusLabel: Record<TaskSummary['status'], string> = {
  open: 'Открыта',
  done: 'Выполнена',
};

const TasksDetail = ({ tasks, tone }: TasksDetailProps) => {
  if (!tasks.length) {
    const empty = getEmptyStateMessage(tone, 'Задачи');
    return <EmptyState title={empty.title} description={empty.description} action={<Button>Добавить задачу</Button>} />;
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.id} className="flex items-center justify-between rounded-lg border border-border bg-surface p-4 shadow-card">
          <div>
            <p className="text-base font-medium text-text">{task.title}</p>
            {task.due_date && <p className="text-xs text-textMuted">Срок: {new Date(task.due_date).toLocaleDateString('ru-RU')}</p>}
          </div>
          <span className="rounded-full border border-border bg-surfaceAlt px-3 py-1 text-xs font-semibold text-textMuted">
            {statusLabel[task.status]}
          </span>
        </div>
      ))}
    </div>
  );
};

export default TasksDetail;
