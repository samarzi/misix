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
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="secondary" onClick={onCreate}>
          Новая категория
        </Button>
      </div>
      {categories.map((category) => (
        <div
          key={category.id}
          className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-300 ease-out-soft hover:-translate-y-1 hover:shadow-glow"
        >
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-3">
                {category.icon && <span className="text-xl">{category.icon}</span>}
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Категория</p>
                  <h3 className="text-lg font-semibold text-text">{category.name}</h3>
                </div>
              </div>
              {category.description && <p className="mt-2 text-sm text-textSecondary">{category.description}</p>}
              {category.color && (
                <span
                  className="mt-3 inline-flex items-center rounded-full border border-borderStrong px-3 py-1 text-xs text-textMuted"
                  style={{ backgroundColor: category.color }}
                >
                  {category.color}
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {category.is_confidential && (
                <span className="rounded-full border border-primary bg-primaryMuted/30 px-3 py-1 text-xs font-semibold text-primary">
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
