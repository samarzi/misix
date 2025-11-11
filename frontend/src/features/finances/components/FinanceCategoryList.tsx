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
    <div className="grid gap-3 md:grid-cols-2">
      {categories.map((category) => (
        <div key={category.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-base font-semibold text-text">{category.name}</h3>
            {category.budget != null && <span className="text-sm text-textMuted">Бюджет: {category.budget}</span>}
          </div>
          <div className="mt-2 flex gap-2">
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
