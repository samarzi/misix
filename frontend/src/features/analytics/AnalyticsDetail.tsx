import type {
  DashboardOverview,
  DashboardStatistics as DashboardStatisticsData,
  FinanceAccount,
  FinanceCategory,
  FinanceTransaction,
} from '../../api/types';
import { formatCurrency, formatMetric } from '../../utils/tone';
import EmptyState from '../../components/EmptyState';
import DashboardStatisticsSection from './components/DashboardStatistics';

interface AnalyticsDetailProps {
  overview?: DashboardOverview | null;
  finances: FinanceTransaction[];
  accounts: FinanceAccount[];
  categories: FinanceCategory[];
  statistics?: DashboardStatisticsData;
}

const AnalyticsDetail = ({ overview, finances, accounts, categories, statistics }: AnalyticsDetailProps) => {
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
    <div className="space-y-5">
      <DashboardStatisticsSection statistics={statistics} />

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Финансовый баланс</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatCurrency(balance)}</p>
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-textSecondary">
            <div className="rounded-xl border border-borderStrong bg-surfaceGlass p-4">
              <span className="block text-xs uppercase tracking-widest text-textMuted">Доходы</span>
              <span className="mt-1 block text-lg font-semibold text-success">{formatCurrency(income)}</span>
            </div>
            <div className="rounded-xl border border-borderStrong bg-surfaceGlass p-4">
              <span className="block text-xs uppercase tracking-widest text-textMuted">Расходы</span>
              <span className="mt-1 block text-lg font-semibold text-danger">{formatCurrency(expense)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Активные задачи</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatMetric(completedTasks)}</p>
          <p className="mt-2 text-sm text-textSecondary">Всего задач: {formatMetric(overview.tasks?.total ?? 0)}</p>
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Долги</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatCurrency(openDebts)}</p>
          <p className="mt-2 text-sm text-textSecondary">Открытых долгов: {formatMetric(overview.debts?.count ?? 0)}</p>
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Напоминания</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatMetric(reminders)}</p>
          <p className="mt-2 text-sm text-textSecondary">
            Следующее событие: {overview.reminders?.nextTriggerAt ? new Date(overview.reminders.nextTriggerAt).toLocaleString('ru-RU') : 'не запланировано'}
          </p>
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow md:col-span-2 xl:col-span-3">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Последние операции</h3>
          {finances.length === 0 ? (
            <p className="mt-4 text-sm text-textSecondary">Добавь первую операцию, чтобы увидеть аналитику.</p>
          ) : (
            <ul className="mt-4 space-y-3 text-sm">
              {finances.slice(0, 5).map((tx) => (
                <li key={tx.id} className="flex items-center justify-between gap-3 rounded-2xl border border-borderStrong bg-surfaceGlass p-4">
                  <div>
                    <p className="font-medium text-text">{tx.description ?? 'Операция'}</p>
                    <p className="text-xs text-textMuted">{new Date(tx.occurred_at).toLocaleString('ru-RU')}</p>
                  </div>
                  <span className={`text-base font-semibold ${tx.amount >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatCurrency(tx.amount)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Счета</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatMetric(accounts.length)}</p>
          <p className="mt-2 text-sm text-textSecondary">Контролируй остатки, чтобы планировать операции.</p>
        </div>

        <div className="rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl transition-all duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
          <h3 className="text-xs uppercase tracking-[0.2em] text-textMuted">Категории</h3>
          <p className="mt-3 text-3xl font-semibold text-text">{formatMetric(categories.length)}</p>
          <p className="mt-2 text-sm text-textSecondary">Категории помогают отслеживать структуру расходов и доходов.</p>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDetail;
