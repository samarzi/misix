import Button from '../../../components/Button';
import type { FinanceTabKey } from '../../../stores/uiStore';

interface FinanceToolbarProps {
  activeTab: FinanceTabKey;
  onTabChange: (tab: FinanceTabKey) => void;
  onAddTransaction: () => void;
  onAddAccount: () => void;
  onAddCategory: () => void;
  onAddRule: () => void;
}

const tabs: { key: FinanceTabKey; label: string }[] = [
  { key: 'overview', label: 'Обзор' },
  { key: 'accounts', label: 'Счета' },
  { key: 'categories', label: 'Категории' },
  { key: 'rules', label: 'Правила' },
];

const FinanceToolbar = ({ activeTab, onTabChange, onAddTransaction, onAddAccount, onAddCategory, onAddRule }: FinanceToolbarProps) => {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-4 shadow-card">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => onTabChange(tab.key)}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              activeTab === tab.key ? 'border-primary bg-primaryMuted text-primary' : 'border-border bg-surfaceAlt text-text'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {activeTab === 'overview' && (
          <Button onClick={onAddTransaction}>Добавить операцию</Button>
        )}
        {activeTab === 'accounts' && (
          <Button onClick={onAddAccount}>Добавить счёт</Button>
        )}
        {activeTab === 'categories' && (
          <Button onClick={onAddCategory}>Добавить категорию</Button>
        )}
        {activeTab === 'rules' && (
          <Button onClick={onAddRule}>Добавить правило</Button>
        )}
      </div>
    </div>
  );
};

export default FinanceToolbar;
