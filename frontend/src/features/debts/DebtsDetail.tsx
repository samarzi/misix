import type { DebtSummary } from '../../api/types';
import EmptyState from '../../components/EmptyState';
import Button from '../../components/Button';
import type { ToneStyle } from '../../config';
import { getEmptyStateMessage } from '../../utils/tone';
import { formatAmount, formatDate } from '../../utils/format';

interface DebtsDetailProps {
  debts: DebtSummary[];
  tone: ToneStyle;
}

const statusLabel: Record<DebtSummary['status'], string> = {
  open: 'Открыт',
  closed: 'Закрыт',
};

const DebtsDetail = ({ debts, tone }: DebtsDetailProps) => {
  if (!debts.length) {
    const empty = getEmptyStateMessage(tone, 'Долги');
    return <EmptyState title={empty.title} description={empty.description} action={<Button>Добавить долг</Button>} />;
  }

  return (
    <div className="space-y-3">
      {debts.map((debt) => (
        <div key={debt.id} className="rounded-lg border border-border bg-surface p-4 shadow-card">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-text">{debt.counterparty}</h3>
              <p className="text-sm text-textMuted">{formatAmount(debt.amount, debt.currency)}</p>
              {debt.due_date && <p className="text-xs text-textMuted">Срок: {formatDate(debt.due_date)}</p>}
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${debt.status === 'open' ? 'border-primary text-primary' : 'border-border text-textMuted'}`}>
              {statusLabel[debt.status]}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DebtsDetail;
