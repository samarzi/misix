import type { NoteSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';

interface NotesDetailProps {
  notes: NoteSummary[];
  tone: ToneStyle;
  onCreate: () => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

const NotesDetail = ({ notes, tone, onCreate, onEdit, onDelete, searchValue, onSearchChange }: NotesDetailProps) => {
  if (!notes.length) {
    const empty = getEmptyStateMessage(tone, 'Заметки');
    return <EmptyState title={empty.title} description={empty.description} action={<Button onClick={onCreate}>Создать заметку</Button>} />;
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <Button variant="secondary" onClick={onCreate}>
          Новая заметка
        </Button>
        <div className="flex items-center gap-2">
          <input
            value={searchValue}
            onChange={(event) => onSearchChange(event.target.value)}
            className="min-w-[220px] rounded-full border border-borderStrong bg-surfaceGlass px-4 py-2 text-sm text-text focus:border-primary focus:outline-none"
            placeholder="Искать по заметкам"
          />
        </div>
      </div>
      {notes.map((note) => (
        <div key={note.id} className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-text">{note.title ?? 'Без названия'}</h3>
              <p className="text-sm text-textSecondary whitespace-pre-wrap">{note.content}</p>
              <p className="text-xs text-textMuted">Создано: {new Date(note.created_at).toLocaleString('ru-RU')}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" onClick={() => onEdit(note.id)}>
                ✏️
              </Button>
              <Button variant="ghost" className="text-danger" onClick={() => onDelete(note.id)}>
                Удалить
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotesDetail;
