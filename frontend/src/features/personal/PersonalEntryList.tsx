import type { PersonalEntry, PersonalCategory } from '../../api/types';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';
import { formatDate } from '../../utils/format';

interface PersonalEntryListProps {
  entries: PersonalEntry[];
  categories: PersonalCategory[];
  onCreate: () => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const dataTypeLabel: Record<PersonalEntry['data_type'], string> = {
  login: 'Доступ',
  contact: 'Контакт',
  document: 'Документ',
  other: 'Другое',
};

const PersonalEntryList = ({ entries, categories, onCreate, onEdit, onDelete }: PersonalEntryListProps) => {
  if (!entries.length) {
    return (
      <EmptyState
        title="Записей пока нет"
        description="Создай первую запись, чтобы хранить доступы, контакты или документы."
        action={<Button onClick={onCreate}>Добавить запись</Button>}
      />
    );
  }

  const categoryMap = new Map(categories.map((category) => [category.id, category.name]));

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="secondary" onClick={onCreate}>
          Новая запись
        </Button>
      </div>
      {entries.map((entry) => (
        <div key={entry.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-textMuted">
                  {dataTypeLabel[entry.data_type]}
                </span>
                {entry.is_favorite && (
                  <span className="rounded-full border border-primary bg-primaryMuted px-3 py-1 text-xs font-semibold text-primary">
                    Избранное
                  </span>
                )}
                {entry.is_confidential && (
                  <span className="rounded-full border border-danger bg-danger/10 px-3 py-1 text-xs font-semibold text-danger">
                    Конфиденциально
                  </span>
                )}
              </div>
              <h3 className="text-base font-semibold text-text">{entry.title}</h3>
              {entry.category_id && (
                <p className="text-sm text-textMuted">Категория: {categoryMap.get(entry.category_id) ?? '—'}</p>
              )}
              {entry.notes && <p className="text-sm text-textMuted">Заметки: {entry.notes}</p>}
              {entry.tags && entry.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 text-xs text-textMuted">
                  {entry.tags.map((tag) => (
                    <span key={tag} className="rounded-full border border-border px-2 py-1">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
              {entry.document_expiry && (
                <p className="text-xs text-textMuted">Действительно до: {formatDate(entry.document_expiry)}</p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" onClick={() => onEdit(entry.id)}>
                ✏️
              </Button>
              <Button variant="ghost" className="text-danger" onClick={() => onDelete(entry.id)}>
                Удалить
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PersonalEntryList;
