import type {
  FinanceAccount,
  FinanceCategory,
  FinanceRule,
  FinanceTransaction,
} from '../../api/types';
import type { FinanceTabKey } from '../../stores/uiStore';
import FinanceToolbar from './components/FinanceToolbar';
import FinanceOverview from './components/FinanceOverview';
import FinanceAccountList from './components/FinanceAccountList';
import FinanceCategoryList from './components/FinanceCategoryList';
import FinanceRuleList from './components/FinanceRuleList';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';

interface FinancesDetailProps {
  transactions: FinanceTransaction[];
  accounts: FinanceAccount[];
  categories: FinanceCategory[];
  rules: FinanceRule[];
  activeTab: FinanceTabKey;
  onTabChange: (tab: FinanceTabKey) => void;
  onCreateTransaction: () => void;
  onEditTransaction: (id: string) => void;
  onDeleteTransaction: (id: string) => void;
  onCreateAccount: () => void;
  onEditAccount: (id: string) => void;
  onDeleteAccount: (id: string) => void;
  onCreateCategory: () => void;
  onEditCategory: (id: string) => void;
  onDeleteCategory: (id: string) => void;
  onCreateRule: () => void;
  onEditRule: (id: string) => void;
  onDeleteRule: (id: string) => void;
  emptyDescription: { title: string; description: string };
}

const FinancesDetail = ({
  transactions,
  accounts,
  categories,
  rules,
  activeTab,
  onTabChange,
  onCreateTransaction,
  onEditTransaction,
  onDeleteTransaction,
  onCreateAccount,
  onEditAccount,
  onDeleteAccount,
  onCreateCategory,
  onEditCategory,
  onDeleteCategory,
  onCreateRule,
  onEditRule,
  onDeleteRule,
  emptyDescription,
}: FinancesDetailProps) => {
  return (
    <div className="space-y-4">
      <FinanceToolbar
        activeTab={activeTab}
        onTabChange={onTabChange}
        onAddTransaction={onCreateTransaction}
        onAddAccount={onCreateAccount}
        onAddCategory={onCreateCategory}
        onAddRule={onCreateRule}
      />

      {activeTab === 'overview' && (
        <FinanceOverview
          transactions={transactions}
          accounts={accounts}
          categories={categories}
          onEditTransaction={onEditTransaction}
          onDeleteTransaction={onDeleteTransaction}
          onCreateTransaction={onCreateTransaction}
          toneDescription={emptyDescription}
        />
      )}

      {activeTab === 'accounts' && (
        <FinanceAccountList accounts={accounts} onEdit={onEditAccount} onDelete={onDeleteAccount} />
      )}

      {activeTab === 'categories' && (
        <FinanceCategoryList categories={categories} onEdit={onEditCategory} onDelete={onDeleteCategory} />
      )}

      {activeTab === 'rules' && <FinanceRuleList rules={rules} onEdit={onEditRule} onDelete={onDeleteRule} />}

      {activeTab !== 'overview' && activeTab !== 'accounts' && activeTab !== 'categories' && activeTab !== 'rules' && (
        <EmptyState
          title="Нет данных"
          description="Выбери доступный раздел меню, чтобы увидеть информацию."
          action={<Button onClick={onCreateTransaction}>Добавить операцию</Button>}
        />
      )}
    </div>
  );
};

export default FinancesDetail;
