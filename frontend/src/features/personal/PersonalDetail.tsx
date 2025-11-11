import type { PersonalCategory, PersonalEntry } from '../../api/types';
import type { ToneStyle } from '../../config';
import PersonalCategoryList from './PersonalCategoryList';
import PersonalEntryList from './PersonalEntryList';

interface PersonalDetailProps {
  entries: PersonalEntry[];
  categories: PersonalCategory[];
  tone: ToneStyle;
  onCreateCategory: () => void;
  onEditCategory: (id: string) => void;
  onDeleteCategory: (id: string) => void;
  onCreateEntry: () => void;
  onEditEntry: (id: string) => void;
  onDeleteEntry: (id: string) => void;
}

const PersonalDetail = ({
  entries,
  categories,
  onCreateCategory,
  onEditCategory,
  onDeleteCategory,
  onCreateEntry,
  onEditEntry,
  onDeleteEntry,
}: PersonalDetailProps) => {
  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <header>
          <h2 className="text-lg font-semibold text-text">Категории</h2>
        </header>
        <PersonalCategoryList
          categories={categories}
          onCreate={onCreateCategory}
          onEdit={onEditCategory}
          onDelete={onDeleteCategory}
        />
      </section>

      <section className="space-y-3">
        <header className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text">Личные записи</h2>
        </header>
        <PersonalEntryList
          entries={entries}
          categories={categories}
          onCreate={onCreateEntry}
          onEdit={onEditEntry}
          onDelete={onDeleteEntry}
        />
      </section>
    </div>
  );
};

export default PersonalDetail;
