import type { FinanceAccount } from '../../../api/types';
import Button from '../../../components/Button';
import EmptyState from '../../../components/EmptyState';
import { formatAmount } from '../../../utils/format';

interface FinanceAccountListProps {
  accounts: FinanceAccount[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const FinanceAccountList = ({ accounts, onEdit, onDelete }: FinanceAccountListProps) => {
  if (!accounts.length) {
    return <EmptyState title="Нет счетов" description="Добавь свой первый счёт, чтобы отслеживать баланс." action={<Button>Добавить счёт</Button>} />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {accounts.map((account) => (
        <div
          key={account.id}
          className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-300 ease-out-soft hover:-translate-y-1 hover:shadow-glow"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Счёт</p>
              <h3 className="text-lg font-semibold text-text">{account.name}</h3>
              <p className="text-sm text-textSecondary">{account.institution ?? 'Без банка'}</p>
            </div>
            <span className="text-xl font-semibold text-text">
              {formatAmount(account.balance)}
            </span>
          </div>
          <div className="mt-5 flex gap-3">
            <Button variant="secondary" onClick={() => onEdit(account.id)}>
              Изменить
            </Button>
            <Button variant="danger" onClick={() => onDelete(account.id)}>
              Удалить
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FinanceAccountList;
