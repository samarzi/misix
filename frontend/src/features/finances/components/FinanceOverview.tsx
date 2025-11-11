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
      <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Последние операции</p>
            <h3 className="text-lg font-semibold text-text">Движение средств</h3>
          </div>
          <Button variant="secondary" className="px-4 py-2" onClick={onCreateTransaction}>
            Добавить
          </Button>
        </div>
        <ul className="mt-4 space-y-3 text-sm">
          {transactions.slice(0, 10).map((transaction) => {
            const account = accounts.find((acc) => acc.id === transaction.account_id);
            const category = categories.find((cat) => cat.id === transaction.category_id);
            return (
              <li
                key={transaction.id}
                className="flex items-center justify-between gap-4 rounded-2xl border border-borderStrong bg-surfaceGlass/80 p-4 transition-transform duration-300 ease-out-soft hover:-translate-y-0.5 hover:bg-surfaceGlass"
              >
                <div>
                  <p className="font-medium text-text">{transaction.description ?? 'Операция'}</p>
                  <p className="text-xs text-textMuted">{formatDateTime(transaction.occurred_at)}</p>
                  <p className="text-xs text-textSecondary">
                    {account?.name ?? 'Счёт неизвестен'} · {category?.name ?? 'Категория не назначена'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-base font-semibold ${transaction.amount >= 0 ? 'text-success' : 'text-danger'}`}
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
