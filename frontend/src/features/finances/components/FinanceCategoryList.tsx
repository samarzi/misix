import type { FinanceCategory } from '../../../api/types';
import Button from '../../../components/Button';
import EmptyState from '../../../components/EmptyState';

interface FinanceCategoryListProps {
  categories: FinanceCategory[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const FinanceCategoryList = ({ categories, onEdit, onDelete }: FinanceCategoryListProps) => {
  if (!categories.length) {
    return <EmptyState title="Категорий пока нет" description="Создай категории, чтобы структурировать расходы." action={<Button>Добавить категорию</Button>} />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {categories.map((category) => (
        <div
          key={category.id}
          className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-300 ease-out-soft hover:-translate-y-1 hover:shadow-glow"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Категория</p>
              <h3 className="text-lg font-semibold text-text">{category.name}</h3>
            </div>
            {category.budget != null && <span className="text-sm text-textSecondary">Бюджет: {category.budget}</span>}
          </div>
          <div className="mt-4 flex gap-3">
            <Button variant="secondary" onClick={() => onEdit(category.id)}>
              Изменить
            </Button>
            <Button variant="danger" onClick={() => onDelete(category.id)}>
              Удалить
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FinanceCategoryList;
