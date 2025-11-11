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
    <div className="grid gap-3 md:grid-cols-2">
      {accounts.map((account) => (
        <div key={account.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-text">{account.name}</h3>
              <p className="text-sm text-textMuted">{account.institution ?? 'Без банка'}</p>
            </div>
            <span className="text-lg font-semibold text-text">{formatAmount(account.balance)}</span>
          </div>
          <div className="mt-4 flex gap-2">
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
