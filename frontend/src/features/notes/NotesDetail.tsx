import type { NoteSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';

interface NotesDetailProps {
  notes: NoteSummary[];
  tone: ToneStyle;
}

const NotesDetail = ({ notes, tone }: NotesDetailProps) => {
  if (!notes.length) {
    const empty = getEmptyStateMessage(tone, 'Заметки');
    return <EmptyState title={empty.title} description={empty.description} action={<Button>Создать заметку</Button>} />;
  }

  return (
    <div className="grid gap-3">
      {notes.map((note) => (
        <div key={note.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <h3 className="text-base font-semibold text-text">{note.title}</h3>
          <p className="mt-1 text-xs text-textMuted">
            Создано: {new Date(note.created_at).toLocaleString('ru-RU')}
          </p>
        </div>
      ))}
    </div>
  );
};

export default NotesDetail;
