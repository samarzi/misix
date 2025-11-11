import type { DashboardStatistics } from '../../../api/types';
import { formatAmount } from '../../../utils/format';

interface DashboardStatisticsSectionProps {
  statistics?: DashboardStatistics;
}

const DashboardStatisticsSection = ({ statistics }: DashboardStatisticsSectionProps) => {
  if (!statistics) {
    return null;
  }

  const topCategories = statistics.finances.topCategoriesLast7;
  const categoryTotals = topCategories.map((item) => Math.abs(item.total));
  const maxCategoryTotal = categoryTotals.length ? Math.max(...categoryTotals) : 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
        <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Задачи · 7 дней</p>
        <p className="mt-3 text-2xl font-semibold text-text">{statistics.tasks.createdLast7}</p>
        <p className="text-sm text-textSecondary">создано</p>
        <p className="mt-2 text-sm text-success">{statistics.tasks.completedLast7} завершено</p>
      </div>

      <div className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
        <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Финансы · 7 дней</p>
        <div className="mt-3 space-y-1 text-sm text-textSecondary">
          <p className="text-success">Доход: {formatAmount(statistics.finances.incomeLast7)}</p>
          <p className="text-danger">Расход: {formatAmount(statistics.finances.expenseLast7)}</p>
        </div>
        <div className="mt-4 space-y-2">
          {topCategories.length === 0 ? (
            <p className="text-xs text-textMuted">Нет активных категорий</p>
          ) : (
            topCategories.slice(0, 4).map((item) => {
              const absoluteTotal = Math.abs(item.total);
              const width = maxCategoryTotal ? Math.max((absoluteTotal / maxCategoryTotal) * 100, 6) : 0;
              return (
                <div key={item.category_id ?? 'uncategorized'}>
                  <div className="flex items-center justify-between text-xs text-textMuted">
                    <span>{item.category_name}</span>
                    <span>{formatAmount(item.total)}</span>
                  </div>
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surfaceGlass">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary via-accent to-accent2"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
        <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Личные данные · 7 дней</p>
        <p className="mt-3 text-2xl font-semibold text-text">{statistics.personal.createdLast7}</p>
        <p className="text-sm text-textSecondary">новых записей</p>
        <p className="mt-2 text-sm text-textMuted">Избранные: {statistics.personal.favorites}</p>
      </div>

      <div className="rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl">
        <p className="text-xs uppercase tracking-[0.2em] text-textMuted">Напоминания · 7 дней</p>
        <p className="mt-3 text-2xl font-semibold text-text">{statistics.reminders.upcoming7Days}</p>
        <p className="text-sm text-textSecondary">запланировано в течение недели</p>
      </div>
    </div>
  );
};

export default DashboardStatisticsSection;
