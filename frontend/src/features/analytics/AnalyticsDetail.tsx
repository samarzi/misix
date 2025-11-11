import type { DashboardOverview, FinanceAccount, FinanceCategory, FinanceTransaction } from '../../api/types';
import { formatCurrency, formatMetric } from '../../utils/tone';
import EmptyState from '../../components/EmptyState';

interface AnalyticsDetailProps {
  overview?: DashboardOverview | null;
  finances: FinanceTransaction[];
  accounts: FinanceAccount[];
  categories: FinanceCategory[];
}

const AnalyticsDetail = ({ overview, finances, accounts, categories }: AnalyticsDetailProps) => {
  if (!overview) {
    return <EmptyState title="Недостаточно данных" description="Сначала обнови дашборд или добавь операции." />;
  }

  const income = overview.finances?.income ?? 0;
  const expense = overview.finances?.expense ?? 0;
  const balance = overview.finances?.balance ?? 0;
  const completedTasks = overview.tasks?.completed ?? 0;
  const openDebts = overview.debts?.openAmount ?? 0;
  const reminders = overview.reminders?.scheduled ?? 0;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Финансовый баланс</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatCurrency(balance)}</p>
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-textMuted">
          <div>
            <span className="block font-medium text-text">Доходы</span>
            <span>{formatCurrency(income)}</span>
          </div>
          <div>
            <span className="block font-medium text-text">Расходы</span>
            <span>{formatCurrency(expense)}</span>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Активные задачи</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatMetric(completedTasks)}</p>
        <p className="mt-1 text-sm text-textMuted">Всего задач: {formatMetric(overview.tasks?.total ?? 0)}</p>
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Долги</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatCurrency(openDebts)}</p>
        <p className="mt-1 text-sm text-textMuted">Открытых долгов: {formatMetric(overview.debts?.count ?? 0)}</p>
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Напоминания</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatMetric(reminders)}</p>
        <p className="mt-1 text-sm text-textMuted">
          Следующее событие: {overview.reminders?.nextTriggerAt ? new Date(overview.reminders.nextTriggerAt).toLocaleString('ru-RU') : 'не запланировано'}
        </p>
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card md:col-span-2">
        <h3 className="text-sm font-semibold text-textMuted">Последние операции</h3>
        {finances.length === 0 ? (
          <p className="mt-2 text-sm text-textMuted">Добавь первую операцию, чтобы увидеть аналитику.</p>
        ) : (
          <ul className="mt-3 space-y-3 text-sm">
            {finances.slice(0, 5).map((tx) => (
              <li key={tx.id} className="flex items-center justify-between rounded-md border border-border bg-surface p-3">
                <div>
                  <p className="font-medium text-text">{tx.description ?? 'Операция'}</p>
                  <p className="text-xs text-textMuted">{new Date(tx.occurred_at).toLocaleString('ru-RU')}</p>
                </div>
                <span className={`text-sm font-semibold ${tx.amount >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatCurrency(tx.amount)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Счета</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatMetric(accounts.length)}</p>
        <p className="mt-1 text-sm text-textMuted">Следи за остатками на счетах для точной аналитики.</p>
      </div>

      <div className="rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
        <h3 className="text-sm font-semibold text-textMuted">Категории</h3>
        <p className="mt-2 text-2xl font-semibold text-text">{formatMetric(categories.length)}</p>
        <p className="mt-1 text-sm text-textMuted">Категории помогают понять структуру расходов и доходов.</p>
      </div>
    </div>
  );
};

export default AnalyticsDetail;
