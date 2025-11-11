import type { FinanceRule } from '../../../api/types';
import Button from '../../../components/Button';
import EmptyState from '../../../components/EmptyState';

interface FinanceRuleListProps {
  rules: FinanceRule[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const FinanceRuleList = ({ rules, onEdit, onDelete }: FinanceRuleListProps) => {
  if (!rules.length) {
    return <EmptyState title="Нет правил" description="Добавь правила, чтобы автоматизировать категоризацию." action={<Button>Создать правило</Button>} />;
  }

  return (
    <div className="space-y-3">
      {rules.map((rule) => (
        <div key={rule.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-text">{rule.name}</h3>
              {rule.description && <p className="text-sm text-textMuted">{rule.description}</p>}
              <p className={`mt-2 inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${rule.is_active ? 'border-primary text-primary' : 'border-border text-textMuted'}`}>
                {rule.is_active ? 'Активно' : 'Выключено'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => onEdit(rule.id)}>
                Изменить
              </Button>
              <Button variant="danger" onClick={() => onDelete(rule.id)}>
                Удалить
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FinanceRuleList;
