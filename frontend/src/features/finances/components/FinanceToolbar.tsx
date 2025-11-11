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
    <div className="flex flex-col gap-5 rounded-2xl border border-borderStrong bg-surface/70 p-6 shadow-card backdrop-blur-xl">
      <div className="flex flex-wrap gap-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => onTabChange(tab.key)}
            className={`group relative overflow-hidden rounded-full border px-4 py-2 text-sm font-medium transition-all duration-350 ease-out-soft ${
              activeTab === tab.key
                ? 'border-primary bg-primaryMuted text-primary shadow-glow'
                : 'border-borderStrong bg-surfaceGlass text-textSecondary hover:text-text'
            }`}
          >
            <span className="pointer-events-none absolute inset-0 translate-x-[-120%] bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.35),transparent)] transition-transform duration-500 group-hover:translate-x-[120%]" aria-hidden="true" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
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
