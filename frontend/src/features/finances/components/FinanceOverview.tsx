import type { FinanceTransaction, FinanceAccount, FinanceCategory } from '../../../api/types';
import Button from '../../../components/Button';
import EmptyState from '../../../components/EmptyState';
import { formatAmount, formatDateTime } from '../../../utils/format';

export interface FinanceOverviewProps {
  transactions: FinanceTransaction[];
  accounts: FinanceAccount[];
  categories: FinanceCategory[];
  onCreateTransaction: () => void;
  onEditTransaction: (id: string) => void;
  onDeleteTransaction: (id: string) => void;
  toneDescription: { title: string; description: string };
}

const FinanceOverview = ({
  transactions,
  accounts,
  categories,
  onCreateTransaction,
  onEditTransaction,
  onDeleteTransaction,
  toneDescription,
}: FinanceOverviewProps) => {
  if (!transactions.length) {
    return (
      <EmptyState
        title={toneDescription.title}
        description={toneDescription.description}
        action={<Button onClick={onCreateTransaction}>Добавить операцию</Button>}
      />
    );
  }

  return (
    <div className="grid gap-4">
      <div className="rounded-lg border border-border bg-surface p-4 shadow-card">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-textMuted">Последние операции</h3>
          <Button variant="secondary" className="px-3 py-1 text-xs" onClick={onCreateTransaction}>
            Добавить
          </Button>
        </div>
        <ul className="mt-3 space-y-3 text-sm">
          {transactions.slice(0, 10).map((transaction) => {
            const account = accounts.find((acc) => acc.id === transaction.account_id);
            const category = categories.find((cat) => cat.id === transaction.category_id);
            return (
              <li
                key={transaction.id}
                className="flex items-center justify-between gap-4 rounded-md border border-border bg-surfaceAlt p-3"
              >
                <div>
                  <p className="font-medium text-text">{transaction.description ?? 'Операция'}</p>
                  <p className="text-xs text-textMuted">{formatDateTime(transaction.occurred_at)}</p>
                  <p className="text-xs text-textMuted">
                    {account?.name ?? 'Счёт неизвестен'} · {category?.name ?? 'Категория не назначена'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-semibold ${transaction.amount >= 0 ? 'text-success' : 'text-danger'}`}
                  >
                    {formatAmount(transaction.amount)}
                  </span>
                  <Button variant="ghost" onClick={() => onEditTransaction(transaction.id)}>
                    ✏️
                  </Button>
                  <Button
                    variant="ghost"
                    className="text-danger"
                    aria-label="Удалить операцию"
                    onClick={() => onDeleteTransaction(transaction.id)}
                  >
                    🗑️
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};

export default FinanceOverview;
