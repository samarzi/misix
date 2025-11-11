import type { PersonalCategory } from '../../api/types';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';

interface PersonalCategoryListProps {
  categories: PersonalCategory[];
  onCreate: () => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const PersonalCategoryList = ({ categories, onCreate, onEdit, onDelete }: PersonalCategoryListProps) => {
  if (!categories.length) {
    return (
      <EmptyState
        title="Категории не созданы"
        description="Добавь категорию, чтобы структурировать личные записи."
        action={<Button onClick={onCreate}>Добавить категорию</Button>}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="secondary" onClick={onCreate}>
          Новая категория
        </Button>
      </div>
      {categories.map((category) => (
        <div key={category.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                {category.icon && <span className="text-lg">{category.icon}</span>}
                <h3 className="text-base font-semibold text-text">{category.name}</h3>
              </div>
              {category.description && <p className="text-sm text-textMuted">{category.description}</p>}
              {category.color && (
                <span
                  className="mt-2 inline-flex items-center rounded-full border border-border px-3 py-1 text-xs text-textMuted"
                  style={{ backgroundColor: category.color }}
                >
                  {category.color}
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {category.is_confidential && (
                <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-primary">
                  Конфиденциально
                </span>
              )}
              <Button variant="ghost" onClick={() => onEdit(category.id)}>
                ✏️
              </Button>
              <Button variant="ghost" className="text-danger" onClick={() => onDelete(category.id)}>
                Удалить
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PersonalCategoryList;
