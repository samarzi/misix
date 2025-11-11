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
    <div className="space-y-4">
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-300 ease-out-soft hover:-translate-y-1 hover:shadow-glow"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Правило</p>
              <h3 className="text-lg font-semibold text-text">{rule.name}</h3>
              {rule.description && <p className="text-sm text-textSecondary">{rule.description}</p>}
              <p className={`mt-3 inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${rule.is_active ? 'border-primary bg-primaryMuted/40 text-primary' : 'border-borderStrong text-textMuted'}`}>
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
