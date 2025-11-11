const SUPABASE_URL = 'https://dcxdnrealygulikpuicm.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjeGRucmVhbHlndWxpa3B1aWNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0NTcwODAsImV4cCI6MjA3ODAzMzA4MH0.M2dsaKFDCnd0w-QCMsHu42KmRKURhvhhwMazM1ybO9Y';
const DEV_BACKEND_HOST = 'http://localhost:8000';
const LOCAL_DEV_PORT = '5173';
const BACKEND_DEV_URL = 'http://localhost:8000';

const LOCAL_HOSTNAMES = new Set(['localhost', '127.0.0.1', '::1']);
const isLocalhost = LOCAL_HOSTNAMES.has(window.location.hostname);
const isDevFrontend = isLocalhost && window.location.port === LOCAL_DEV_PORT;

function normalizeBackendUrl(value) {
  if (!value) return null;

  try {
    const decoded = decodeURIComponent(value);
    if (/^https?:\/\//i.test(decoded)) {
      return decoded.replace(/\/$/, "");
    }

function renderModal(modalState) {
  const baseActions = `
    <div class="modal-actions">
      <span class="spacer"></span>
      <button type="button" class="secondary" data-action="modal-cancel">Отмена</button>
      <button type="button" data-action="modal-confirm">Сохранить</button>
    </div>
  `;

  if (modalState.type === 'transaction') {
    const { payload = {}, accounts = [], categories = [], isEdit } = modalState;
    const title = tone('transactionFormTitle', { isEdit });
    return renderGenericModal({
      title,
      body: renderTransactionForm({ payload, accounts, categories }),
      actions: baseActions,
      error: modalState.error,
    });
  }

  if (modalState.type === 'account') {
    const { payload = {}, isEdit } = modalState;
    const title = tone('accountFormTitle', { isEdit });
    return renderGenericModal({
      title,
      body: renderAccountForm(payload),
      actions: baseActions,
      error: modalState.error,
    });
  }

  if (modalState.type === 'category') {
    const { payload = {}, isEdit } = modalState;
    const title = tone('categoryFormTitle', { isEdit });
    return renderGenericModal({
      title,
      body: renderCategoryForm(payload),
      actions: baseActions,
      error: modalState.error,
    });
  }

  if (modalState.type === 'rule') {
    const { payload = {}, categories = [], isEdit } = modalState;
    const title = tone('ruleFormTitle', { isEdit });
    return renderGenericModal({
      title,
      body: renderRuleForm({ payload, categories }),
      actions: baseActions,
      error: modalState.error,
    });
  }

  if (modalState.type === 'purge-category') {
    const { category, options = {} } = modalState;
    const title = tone('purgeConfirmTitle', { name: category.name });
    const body = `
      <div class="modal-section">
        <p>${tone('purgeConfirmHint')}</p>
        <label><input type="checkbox" data-field="remove_transactions" ${options.remove_transactions !== false ? 'checked' : ''}> Удалить операции</label>
        <label><input type="checkbox" data-field="remove_debts" ${options.remove_debts ? 'checked' : ''}> Удалить долги</label>
        <label><input type="checkbox" data-field="remove_rules" ${options.remove_rules ? 'checked' : ''}> Удалить правила</label>
      </div>
    `;
    const actions = `
      <div class="modal-actions">
        <button type="button" class="secondary" data-action="modal-cancel">Отмена</button>
        <button type="button" class="danger" data-action="modal-purge-confirm">Очистить</button>
      </div>
    `;
    return renderGenericModal({ title, body, actions, error: modalState.error });
  }

  return '';
}

function renderGenericModal({ title, body, actions, error }) {
  return `
    <div class="modal-backdrop">
      <div class="modal bounce-in">
        <h3>${title}</h3>
        ${error ? `<div class="notice error">${error}</div>` : ''}
        <div class="modal-section">
          ${body}
        </div>
        ${actions}
      </div>
    </div>
  `;
}

function renderTransactionForm({ payload, accounts, categories }) {
  const { amount = '', account_id = '', type = 'expense', category_id = '', description = '', merchant = '', payment_method = '', tags = [], transaction_date = '', notes = '' } = payload;
  const tagsValue = Array.isArray(tags) ? tags.join(', ') : '';
  return `
    <label>
      Сумма
      <input type="number" step="0.01" data-field="amount" value="${amount}" placeholder="0.00" required>
    </label>
    <div class="grid two">
      <label>
        Счёт
        <select data-field="account_id" required>
          <option value="">Выбери счёт</option>
          ${accounts.map((acc) => `<option value="${acc.id}" ${acc.id === account_id ? 'selected' : ''}>${acc.name}</option>`).join('')}
        </select>
      </label>
      <label>
        Тип
        <select data-field="type">
          <option value="income" ${type === 'income' ? 'selected' : ''}>Доход</option>
          <option value="expense" ${type === 'expense' ? 'selected' : ''}>Расход</option>
        </select>
      </label>
    </div>
    <label>
      Категория
      <select data-field="category_id" required>
        <option value="">Выбери категорию</option>
        ${categories.map((cat) => `<option value="${cat.id}" ${cat.id === category_id ? 'selected' : ''}>${cat.name}</option>`).join('')}
      </select>
    </label>
    <label>
      Описание
      <input type="text" data-field="description" value="${description}" placeholder="Например, оплата кофе">
    </label>
    <label>
      Продавец/мерчант
      <input type="text" data-field="merchant" value="${merchant}" placeholder="Кофейня, магазин">
    </label>
    <label>
      Способ оплаты
      <input type="text" data-field="payment_method" value="${payment_method}" placeholder="Карта, наличные">
    </label>
    <label>
      Теги
      <input type="text" data-field="tags" value="${tagsValue}" placeholder="через запятую">
    </label>
    <label>
      Дата операции
      <input type="datetime-local" data-field="transaction_date" value="${toInputDateTime(transaction_date)}">
    </label>
    <label>
      Заметка
      <textarea data-field="notes" rows="3">${notes || ''}</textarea>
    </label>
  `;
}

function renderAccountForm(payload = {}) {
  const { name = '', account_type = 'other', currency = 'RUB', balance = '', color = '', icon = '', is_archived = false } = payload;
  return `
    <label>
      Название счёта
      <input type="text" data-field="name" value="${name}" placeholder="Например, Сбербанк" required>
    </label>
    <div class="grid two">
      <label>
        Тип
        <select data-field="account_type">
          ${ACCOUNT_TYPE_OPTIONS.map((option) => `<option value="${option.value}" ${option.value === account_type ? 'selected' : ''}>${option.label}</option>`).join('')}
        </select>
      </label>
      <label>
        Валюта
        <input type="text" data-field="currency" value="${currency || 'RUB'}" placeholder="RUB" maxlength="3">
      </label>
    </div>
    <label>
      Баланс (опционально)
      <input type="number" step="0.01" data-field="balance" value="${balance === null || balance === undefined ? '' : balance}">
    </label>
    <label>
      Цвет
      <input type="text" data-field="color" value="${color || ''}" placeholder="#4587F8">
    </label>
    <label>
      Иконка
      <input type="text" data-field="icon" value="${icon || ''}" placeholder="🏦">
    </label>
    <label class="checkbox">
      <input type="checkbox" data-field="is_archived" ${is_archived ? 'checked' : ''}> Архивировать счёт
    </label>
  `;
}

function renderCategoryForm(payload = {}) {
  const { name = '', type = 'expense', color = '', icon = '', parent_id = null } = payload;
  const categories = state.financeCategories || [];
  return `
    <label>
      Название категории
      <input type="text" data-field="name" value="${name}" placeholder="Например, Продукты" required>
    </label>
    <label>
      Тип категории
      <select data-field="type">
        <option value="income" ${type === 'income' ? 'selected' : ''}>Доход</option>
        <option value="expense" ${type === 'expense' ? 'selected' : ''}>Расход</option>
      </select>
    </label>
    <label>
      Цвет
      <input type="text" data-field="color" value="${color || ''}" placeholder="#FF6B6B">
    </label>
    <label>
      Иконка
      <input type="text" data-field="icon" value="${icon || ''}" placeholder="🛒">
    </label>
    <label>
      Родительская категория (опционально)
      <select data-field="parent_id">
        <option value="">Без родителя</option>
        ${categories
          .filter((category) => category.id !== payload.id)
          .map((category) => `<option value="${category.id}" ${category.id === parent_id ? 'selected' : ''}>${category.name}</option>`)
          .join('')}
      </select>
    </label>
  `;
}

function renderRuleForm({ payload = {}, categories = [] }) {
  const { match_type = 'merchant', match_pattern = '', category_id = '', confidence = 1, is_active = true } = payload;
  return `
    <label>
      Что узнаём
      <select data-field="match_type">
        ${RULE_MATCH_TYPES.map((rule) => `<option value="${rule.value}" ${rule.value === match_type ? 'selected' : ''}>${rule.label}</option>`).join('')}
      </select>
    </label>
    <label>
      Значение
      <input type="text" data-field="match_pattern" value="${match_pattern}" placeholder="Например, Кофейня Питер" required>
    </label>
    <label>
      Категория
      <select data-field="category_id" required>
        <option value="">Выбери категорию</option>
        ${categories.map((category) => `<option value="${category.id}" ${category.id === category_id ? 'selected' : ''}>${category.name}</option>`).join('')}
      </select>
    </label>
    <label>
      Уверенность (0-1)
      <input type="number" step="0.05" min="0" max="1" data-field="confidence" value="${confidence}">
    </label>
    <label class="checkbox">
      <input type="checkbox" data-field="is_active" ${is_active ? 'checked' : ''}> Правило активно
    </label>
  `;
}
  } catch (error) {
    // ignore decode errors and fall back to raw value
  }

  if (/^https?:\/\//i.test(value)) {
    return value.replace(/\/$/, "");
  }

  return null;
}

function getBackendUrlFromContext() {
  // 1) Explicit global override (can be injected before app.js)
  if (typeof window.MISIX_BACKEND_URL === "string") {
    const fromGlobal = normalizeBackendUrl(window.MISIX_BACKEND_URL);
    if (fromGlobal) return fromGlobal;
  }

  // 2) Query string ?backend=https://...
  const searchParams = new URLSearchParams(window.location.search);
  const backendFromQuery = normalizeBackendUrl(searchParams.get("backend"));
  if (backendFromQuery) return backendFromQuery;

  // 3) Hash #backend=https://...
  const hash = window.location.hash?.replace(/^#/, "");
  if (hash) {
    const hashParams = new URLSearchParams(hash);
    const backendFromHash = normalizeBackendUrl(hashParams.get("backend"));
    if (backendFromHash) return backendFromHash;
  }

  // 4) Telegram WebApp start_param: backend=<url-encoded>
  const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
  if (typeof startParam === "string" && startParam.length > 0) {
    // Allow either "backend=<encoded>" or direct encoded URL string
    const params = new URLSearchParams(startParam.replace(/;/g, "&"));
    const backendFromStart = normalizeBackendUrl(params.get("backend") || startParam);
    if (backendFromStart) return backendFromStart;
  }

  return null;
}

const dynamicBackendUrl = getBackendUrlFromContext();

const BACKEND_BASE_URL =
  dynamicBackendUrl
  || (isDevFrontend ? BACKEND_DEV_URL : `${window.location.protocol}//${window.location.host}`);

let supabaseClient = null;

const DEV_MODE_PASSWORD = '8985';
const DEV_MODE_PROFILE = {
  telegramId: 1346574159,
  username: 't0g0r0t',
  fullName: 'samarzi',
};

const TONE_STORAGE_KEY = 'misix_tone_style';

const DASHBOARD_SECTIONS = [
  {
    key: 'analytics',
    icon: '📊',
    title: 'Аналитика',
    summary: () => {
      const overview = state.overview;
      if (!overview) {
        return {
          primary: 'Нет данных',
          secondary: 'Обнови дашборд для аналитики',
        };
      }

      const totalTasks = overview.tasks?.total ?? 0;
      const completedTasks = overview.tasks?.completed ?? 0;
      const balance = overview.finances?.balance ?? 0;
      const openDebts = overview.debts?.openAmount ?? 0;
      const reminders = overview.reminders?.scheduled ?? 0;

      return {
        primary: `${formatNumber(completedTasks)} из ${formatNumber(totalTasks)} задач решено`,
        secondary: `Баланс ${formatAmount(balance)} · Долги ${formatAmount(openDebts)} · Напоминаний ${formatNumber(reminders)}`,
      };
    },
    render: renderAnalyticsDetail,
  },
  {
    key: 'tasks',
    icon: '🗂️',
    title: 'Задачи',
    summary: () => {
      const total = state.overview?.tasks?.total ?? state.tasks.length;
      const open = state.overview?.tasks?.open ?? 0;
      const done = state.overview?.tasks?.completed ?? 0;
      return {
        primary: `${total} ${pluralize(total, ['задача', 'задачи', 'задач'])}`,
        secondary: total ? `В работе: ${open} · Готово: ${done}` : 'Нет задач',
      };
    },
    render: renderTasksDetail,
  },
  {
    key: 'notes',
    icon: '📝',
    title: 'Заметки',
    summary: () => {
      const total = state.overview?.notes?.total ?? state.notes.length;
      const personal = state.overview?.personal?.total ?? 0;
      return {
        primary: `${total} ${pluralize(total, ['заметка', 'заметки', 'заметок'])}`,
        secondary: personal ? `Личных: ${personal}` : 'Личных записей нет',
      };
    },
    render: renderNotesDetail,
  },
  {
    key: 'finances',
    icon: '💰',
    title: 'Финансы',
    summary: () => {
      const balance = state.overview?.finances?.balance;
      const income = state.overview?.finances?.income;
      const expense = state.overview?.finances?.expense;
      return {
        primary: balance != null ? formatAmount(balance) : 'Баланс неизвестен',
        secondary: income != null && expense != null
          ? `Доходы ${formatAmount(income)} · Расходы ${formatAmount(expense)}`
          : 'Попробуй добавить операции',
      };
    },
    render: renderFinancesDetail,
  },
  {
    key: 'debts',
    icon: '📉',
    title: 'Долги',
    summary: () => {
      const openCount = state.overview?.debts?.openCount ?? 0;
      const openAmount = state.overview?.debts?.openAmount;
      return {
        primary: `${openCount} открыто`,
        secondary: openAmount ? `Сумма ${formatAmount(openAmount)}` : 'Задолженностей нет',
      };
    },
    render: renderDebtsDetail,
  },
  {
    key: 'reminders',
    icon: '⏰',
    title: 'Напоминания',
    summary: () => {
      const scheduled = state.overview?.reminders?.scheduled ?? state.reminders.length;
      const next = state.overview?.reminders?.next;
      return {
        primary: `${scheduled} активных`,
        secondary: next ? `Ближайшее: ${formatDateTime(next)}` : 'Не запланировано',
      };
    },
    render: renderRemindersDetail,
  },
  {
    key: 'sleep',
    icon: '😴',
    title: 'Сон',
    summary: () => {
      const sessions = state.sleepSessions.length;
      return {
        primary: `${sessions} ${pluralize(sessions, ['сессия', 'сессии', 'сессий'])}`,
        secondary: sessions ? 'Последние результаты внутри' : 'Нет записей сна',
      };
    },
    render: renderSleepDetail,
  },
  {
    key: 'health',
    icon: '🩺',
    title: 'Здоровье',
    summary: () => {
      const metrics = state.healthMetrics.length;
      return {
        primary: `${metrics} ${pluralize(metrics, ['метрика', 'метрики', 'метрик'])}`,
        secondary: metrics ? 'Последние измерения внутри' : 'Нет измерений',
      };
    },
    render: renderHealthDetail,
  },
  {
    key: 'personal',
    icon: '🔐',
    title: 'Личные данные',
    summary: () => {
      const entries = state.personalEntries.length;
      return {
        primary: `${entries} ${pluralize(entries, ['запись', 'записи', 'записей'])}`,
        secondary: entries ? 'Полные детали внутри' : 'Пока пусто',
      };
    },
    render: renderPersonalDataDetail,
  },
];

function pluralize(count, forms) {
  const n = Math.abs(count) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return forms[2];
  if (n1 > 1 && n1 < 5) return forms[1];
  if (n1 === 1) return forms[0];
  return forms[2];
}

const TONE_LIBRARY = {
  neutral: {
    greeting: ({ name }) => `Привет, ${name} 👋`,
    subtitleReady: ({ timestamp }) => `Обновлено ${timestamp}`,
    subtitlePending: () => 'Данные появятся после синхронизации',
    financesEmpty: () => 'Когда добавишь доходы или расходы, они появятся здесь.',
    accountsEmpty: () => 'Пока нет ни одного счёта — добавь первый, чтобы навести порядок.',
    categoriesEmpty: () => 'Классические категории уже здесь, но ты можешь создать свои.',
    rulesEmpty: () => 'Здесь будут правила автокатегоризации. Пока нечего запоминать.',
    transactionFormTitle: ({ isEdit }) => (isEdit ? 'Изменить операцию' : 'Новая операция'),
    debtFormTitle: ({ isEdit }) => (isEdit ? 'Изменить долг' : 'Новый долг'),
    accountFormTitle: ({ isEdit }) => (isEdit ? 'Изменить счёт' : 'Новый счёт'),
    categoryFormTitle: ({ isEdit }) => (isEdit ? 'Изменить категорию' : 'Новая категория'),
    ruleFormTitle: ({ isEdit }) => (isEdit ? 'Изменить правило' : 'Новое правило'),
    purgeConfirmTitle: ({ name }) => `Очистка «${name}»`,
    purgeConfirmHint: () => 'Выбери, что именно удалить для этой категории.',
    teasingToggle: () => 'Подкалывающий',
    businessToggle: () => 'Деловой',
    neutralToggle: () => 'Нейтральный',
  },
  teasing: {
    greeting: ({ name }) => `О, ${name}, опять пришёл считать копейки? 😏`,
    subtitleReady: ({ timestamp }) => `Я всё пересчитал. Последняя проверка была ${timestamp}.`,
    subtitlePending: () => 'Да-да, данные где-то едут. Терпение, миллионер.',
    financesEmpty: () => 'Ноль операций — вот это уровень минимализма. Может, добавишь хоть что-нибудь?',
    accountsEmpty: () => 'Счётов нет. Думаешь, под матрасом надёжнее?',
    categoriesEmpty: () => 'Категорий мало. Неужели все траты — одна сплошная «Потратил»?',
    rulesEmpty: () => 'Без правил я каждый раз буду мучить тебя вопросами. Ну-ну.',
    transactionFormTitle: ({ isEdit }) => (isEdit ? 'Правим твою легендарную операцию' : 'Бросай ещё монетку'),
    debtFormTitle: ({ isEdit }) => (isEdit ? 'Подшаманим долг' : 'Запиши, кто кому должен'),
    accountFormTitle: ({ isEdit }) => (isEdit ? 'Правка счёта' : 'Создаём новый кошелёк'),
    categoryFormTitle: ({ isEdit }) => (isEdit ? 'Категория получает апгрейд' : 'Придумай новую категорию'),
    ruleFormTitle: ({ isEdit }) => (isEdit ? 'Правило, второй дубль' : 'Добавим правило, раз память не вечна'),
    purgeConfirmTitle: ({ name }) => `Вычищаем «${name}»?`,
    purgeConfirmHint: () => 'Последний шанс перед большим уборочным разгромом.',
    teasingToggle: () => 'Подкалывающий (активен)',
    businessToggle: () => 'Деловой',
    neutralToggle: () => 'Нейтральный',
  },
  business: {
    greeting: ({ name }) => `Здравствуйте, ${name}.`,
    subtitleReady: ({ timestamp }) => `Обновлено ${timestamp}.`,
    subtitlePending: () => 'Данные готовятся к отображению.',
    financesEmpty: () => 'Операций нет. Добавьте первую для учёта.',
    accountsEmpty: () => 'Создайте финансовый счёт, чтобы вести учёт средств.',
    categoriesEmpty: () => 'Категорий нет. Создайте необходимую структуру.',
    rulesEmpty: () => 'Правила категорий отсутствуют. Добавьте, чтобы ускорить классификацию.',
    transactionFormTitle: ({ isEdit }) => (isEdit ? 'Редактирование операции' : 'Новая операция'),
    debtFormTitle: ({ isEdit }) => (isEdit ? 'Редактирование долга' : 'Новый долг'),
    accountFormTitle: ({ isEdit }) => (isEdit ? 'Редактирование счёта' : 'Новый счёт'),
    categoryFormTitle: ({ isEdit }) => (isEdit ? 'Редактирование категории' : 'Новая категория'),
    ruleFormTitle: ({ isEdit }) => (isEdit ? 'Редактирование правила' : 'Новое правило'),
    purgeConfirmTitle: ({ name }) => `Очистка данных категории «${name}»`,
    purgeConfirmHint: () => 'Выберите элементы для удаления.',
    teasingToggle: () => 'Подкалывающий',
    businessToggle: () => 'Деловой (активен)',
    neutralToggle: () => 'Нейтральный',
  },
};

function resolveToneTemplate(key) {
  const toneKey = state.toneStyle in TONE_LIBRARY ? state.toneStyle : 'neutral';
  const tonePack = TONE_LIBRARY[toneKey];
  if (tonePack && tonePack[key] != null) return tonePack[key];
  return TONE_LIBRARY.neutral[key];
}

function tone(key, params = {}) {
  const template = resolveToneTemplate(key);
  if (typeof template === 'function') {
    return template(params);
  }
  return template != null ? template : (params.fallback ?? '');
}

const ACCOUNT_TYPE_OPTIONS = [
  { value: 'cash', label: 'Наличные' },
  { value: 'bank', label: 'Банковский счёт' },
  { value: 'card', label: 'Дебетовая карта' },
  { value: 'credit_card', label: 'Кредитная карта' },
  { value: 'e_wallet', label: 'Электронный кошелёк' },
  { value: 'savings', label: 'Накопительный счёт' },
  { value: 'other', label: 'Другое' },
];

const ACCOUNT_TYPE_LABELS = ACCOUNT_TYPE_OPTIONS.reduce((acc, option) => {
  acc[option.value] = option.label;
  return acc;
}, {});

const RULE_MATCH_TYPES = [
  { value: 'merchant', label: 'По продавцу' },
  { value: 'description', label: 'По описанию' },
  { value: 'tag', label: 'По тегу' },
  { value: 'counterparty', label: 'По контрагенту' },
];

const DEBT_STATUS_OPTIONS = [
  { value: 'pending', label: 'В ожидании' },
  { value: 'paid', label: 'Закрыт' },
  { value: 'overdue', label: 'Просрочен' },
  { value: 'cancelled', label: 'Отменён' },
];

const DEBT_DIRECTION_OPTIONS = [
  { value: 'owed_by_me', label: 'Я должен' },
  { value: 'owed_to_me', label: 'Мне должны' },
];

function toInputDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  const tzOffsetMinutes = date.getTimezoneOffset();
  const local = new Date(date.getTime() - tzOffsetMinutes * 60000);
  return local.toISOString().slice(0, 16);
}

function fromInputDateTime(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
}

async function apiRequest(path, options = {}) {
  const { method = 'GET' } = options;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const requestInit = {
    method,
    headers,
    ...options,
  };

  if (requestInit.body && typeof requestInit.body !== 'string') {
    requestInit.body = JSON.stringify(requestInit.body);
  }

  const response = await fetch(`${BACKEND_BASE_URL}${path}`, requestInit);
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data?.detail || data?.message || JSON.stringify(data);
    } catch {
      try {
        message = await response.text();
      } catch {
        // ignore
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('Content-Type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }

  return response.text();
}

function openModal(modalState) {
  setState({ modal: { error: null, ...modalState } });
}

function closeModal() {
  if (!state.modal) return;
  setState({ modal: null });
}

function setModalError(message) {
  if (!state.modal) return;
  setState({ modal: { ...state.modal, error: message } });
}

const state = {
  userId: null,
  userLabel: null,
  loading: false,
  error: null,
  view: 'summary',
  detailSection: null,
  financeView: 'overview',
  showSettingsModal: false,
  settingsMode: null,
  passwordConfigured: false,
  securityQuestion: null,
  securityAnswer: null,
  passwordHash: null,
  pinEntry: ['', '', '', ''],
  pinError: null,
  pinStep: 'enter',
  pendingAction: null,
  tmpPin: null,
  unlocked: false,
  overview: null,
  tasks: [],
  notes: [],
  finances: [],
  debts: [],
  reminders: [],
  sleepSessions: [],
  healthMetrics: [],
  personalEntries: [],
  messages: [],
  financeCategories: [],
  financeAccounts: [],
  financeCategoryRules: [],
  healthFilterType: 'all',
  healthFilterPeriod: '30',
  lastUpdated: null,
  toneStyle: 'neutral',
  modal: null,
};

const SECURITY_STORAGE_KEYS = {
  hash: 'misix_pin_hash',
  question: 'misix_pin_question',
  answer: 'misix_pin_answer',
};

function hydrateSecurityState() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  const storedHash = window.localStorage.getItem(SECURITY_STORAGE_KEYS.hash);
  const storedQuestion = window.localStorage.getItem(SECURITY_STORAGE_KEYS.question);
  const storedAnswer = window.localStorage.getItem(SECURITY_STORAGE_KEYS.answer);

  if (storedHash) {
    state.passwordConfigured = true;
    state.passwordHash = storedHash;
    state.securityQuestion = storedQuestion || null;
    state.securityAnswer = storedAnswer || null;
  }
}

function persistSecurityToStorage() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  if (state.passwordConfigured && state.passwordHash) {
    window.localStorage.setItem(SECURITY_STORAGE_KEYS.hash, state.passwordHash);
    if (state.securityQuestion) {
      window.localStorage.setItem(SECURITY_STORAGE_KEYS.question, state.securityQuestion);
    }
    if (state.securityAnswer) {
      window.localStorage.setItem(SECURITY_STORAGE_KEYS.answer, state.securityAnswer);
    }
  } else {
    clearSecurityFromStorage();
  }
}

function clearSecurityFromStorage() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }
  window.localStorage.removeItem(SECURITY_STORAGE_KEYS.hash);
  window.localStorage.removeItem(SECURITY_STORAGE_KEYS.question);
  window.localStorage.removeItem(SECURITY_STORAGE_KEYS.answer);
}

hydrateSecurityState();
state.unlocked = !state.passwordConfigured;

function resetSecuritySettings() {
  state.passwordHash = null;
  state.passwordConfigured = false;
  state.securityQuestion = null;
  state.securityAnswer = null;
  persistSecurityToStorage();
}

const UUID_REGEX = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isUuid(value) {
  return UUID_REGEX.test(value);
}

function isTelegramWebApp() {
  const webApp = window.Telegram?.WebApp;
  if (!webApp) {
    return false;
  }

  if (webApp.initDataUnsafe?.user) {
    return true;
  }

  const platform = webApp.platform;
  if (platform && platform !== 'unknown') {
    return true;
  }

  return false;
}

function isTelegramId(value) {
  return /^\d+$/.test(value);
}

function formatDisplayName(labelInput, userData, telegramId) {
  if (labelInput) return labelInput;
  if (userData?.full_name) return userData.full_name;
  if (userData?.username) return `@${userData.username}`;
  if (userData?.first_name || userData?.last_name) {
    return `${userData.first_name || ''} ${userData.last_name || ''}`.trim();
  }
  return `tg:${telegramId}`;
}

function initSupabase() {
  if (!supabaseClient) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
}

function setState(patch) {
  Object.assign(state, patch);
  render();
}

function resetPinEntry(step = 'enter') {
  state.pinEntry = ['', '', '', ''];
  state.pinError = null;
  state.pinStep = step;
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${formatDate(date)} ${date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`;
}

function formatSensitive(value) {
  if (!value) return '—';
  if (typeof value === 'string' && value.startsWith('gAAAA')) {
    return '🔐 Скрыто (доступно через защищённый канал)';
  }
  return value;
}

function parseDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function getUniqueMetricTypes(metrics) {
  const types = new Set(metrics.map((metric) => metric.metric_type).filter(Boolean));
  return Array.from(types);
}

function filterHealthMetrics(metrics) {
  if (!metrics || metrics.length === 0) {
    return [];
  }

  const { healthFilterType, healthFilterPeriod } = state;
  const days = Number.parseInt(healthFilterPeriod, 10) || 30;
  const threshold = new Date();
  threshold.setDate(threshold.getDate() - days);

  return metrics.filter((metric) => {
    if (healthFilterType !== 'all' && metric.metric_type !== healthFilterType) {
      return false;
    }

    const recordedAt = parseDate(metric.recorded_at || metric.created_at);
    if (!recordedAt) {
      return true;
    }

    return recordedAt >= threshold;
  }).sort((a, b) => {
    const dateA = parseDate(a.recorded_at || a.created_at) || new Date(0);
    const dateB = parseDate(b.recorded_at || b.created_at) || new Date(0);
    return dateA - dateB;
  });
}

function computeHealthSummary(metrics) {
  if (!metrics || metrics.length === 0) {
    return null;
  }

  const values = metrics.map((metric) => Number(metric.metric_value)).filter((value) => !Number.isNaN(value));
  if (values.length === 0) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((acc, value) => acc + value, 0) / values.length;
  const first = values[0];
  const last = values[values.length - 1];

  return {
    min,
    max,
    avg,
    delta: last - first,
    latest: last,
  };
}

function buildSparklineSvg(metrics) {
  if (!metrics || metrics.length === 0) {
    return '';
  }

  const values = metrics
    .map((metric) => Number(metric.metric_value))
    .filter((value) => !Number.isNaN(value));

  if (values.length === 0) {
    return '';
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${Math.round(x * 100) / 100},${Math.round(y * 100) / 100}`;
  }).join(' ');

  return `
    <svg class="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline points="${points}" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  `;
}

function formatAmount(amount) {
  if (amount == null) return '—';
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(Number(amount));
}

async function loadData() {
  if (!state.userId) return;
  if (state.passwordConfigured && !state.unlocked) {
    return;
  }
  setState({ loading: true, error: null });

  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/dashboard/summary?user_id=${encodeURIComponent(state.userId)}`);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Backend ${response.status}: ${text}`);
    }

    const data = await response.json();

    setState({
      loading: false,
      error: null,
      overview: data.overview ?? null,
      tasks: data.tasks ?? [],
      notes: data.notes ?? [],
      finances: data.finances ?? [],
      debts: data.debts ?? [],
      reminders: data.reminders ?? [],
      sleepSessions: data.sleepSessions ?? [],
      healthMetrics: data.healthMetrics ?? [],
      personalEntries: data.personalEntries ?? [],
      messages: data.messages ?? [],
      financeCategories: data.financeCategories ?? [],
      financeAccounts: data.financeAccounts ?? [],
      financeCategoryRules: data.financeCategoryRules ?? [],
      lastUpdated: new Date(),
    });
  } catch (error) {
    console.error('Failed to load data', error);
    const reason = error instanceof Error ? error.message : JSON.stringify(error);
    setState({
      loading: false,
      error: `Не удалось загрузить данные: ${reason}`,
    });
  }
}

function logout() {
  setState({
    userId: null,
    userLabel: null,
    view: 'summary',
    unlocked: !state.passwordConfigured,
    overview: null,
    tasks: [],
    notes: [],
    finances: [],
    debts: [],
    reminders: [],
    sleepSessions: [],
    lastUpdated: null,
    error: null,
    financeAccounts: [],
    financeCategoryRules: [],
    financeCategories: [],
  });
}

function formatNumber(value, options = {}) {
  if (value == null || Number.isNaN(Number(value))) return '—';
  const formatter = new Intl.NumberFormat('ru-RU', options);
  return formatter.format(value);
}

function renderLogin() {
  const devModeAvailable = !isTelegramWebApp();
  return `
    <div class="login-wrapper card">
      <h1>MISIX</h1>
      <p>Авторизуйтесь через Telegram WebApp.</p>
      <form id="login-form">
        <button type="button" class="secondary" id="tg-login">Войти через Telegram</button>
        ${devModeAvailable ? '<button type="button" id="dev-login">Режим разработчика</button>' : ''}
      </form>
    </div>
  `;
}

function renderToolbar() {
  const name = state.userLabel ? state.userLabel : state.userId || 'друг';
  const timestamp = state.lastUpdated
    ? `${formatDate(state.lastUpdated)} ${state.lastUpdated.toLocaleTimeString('ru-RU')}`
    : null;
  const subtitle = timestamp
    ? tone('subtitleReady', { timestamp })
    : tone('subtitlePending');
  const greeting = tone('greeting', { name });

  const toneButtons = [
    { key: 'neutral', label: tone('neutralToggle') },
    { key: 'teasing', label: tone('teasingToggle') },
    { key: 'business', label: tone('businessToggle') },
  ].map(({ key, label }) => {
    const active = state.toneStyle === key ? 'active' : '';
    return `<button type="button" class="chip ${active}" data-action="tone-select" data-tone="${key}">${label}</button>`;
  }).join('');

  return `
    <div class="card">
      <div class="section-header">
        <div>
          <h2 class="glow">${greeting}</h2>
          <small>${subtitle}</small>
        </div>
        <div class="toolbar">
          <button type="button" id="refresh-btn">Обновить</button>
          <button type="button" class="secondary" id="logout-btn">Выйти</button>
        </div>
      </div>
      <div class="tone-toggle">
        ${toneButtons}
      </div>
      <div class="notice${state.loading ? '' : ' hidden'}">Обновляю данные...</div>
      ${state.error ? `<div class="notice error">${state.error}</div>` : ''}
    </div>
  `;
}

function renderDetailView() {
  const section = DASHBOARD_SECTIONS.find((item) => item.key === state.detailSection);
  if (!section) {
    return `
      <div class="card">
        <div class="section-header">
          <h3>Раздел не найден</h3>
          <button type="button" class="secondary" data-action="back-to-summary">Назад</button>
        </div>
        <div class="empty">Похоже, модуль ещё не реализован.</div>
      </div>
    `;
  }

  const summary = section.summary();

  return `
    <div class="card detail-header">
      <div class="section-header">
        <div class="detail-title">
          <span class="detail-icon">${section.icon}</span>
          <div>
            <h3>${section.title}</h3>
            <small>${summary.primary}</small>
            <small>${summary.secondary}</small>
          </div>
        </div>
        <button type="button" class="secondary" data-action="back-to-summary">← Назад</button>
      </div>
    </div>
    ${section.render()}
  `;
}

function renderAnalyticsDetail() {
  const overview = state.overview;
  if (!overview) {
    return `
      <div class="card">
        <div class="empty">Аналитика появится после синхронизации данных.</div>
      </div>
    `;
  }

  const metrics = buildOverviewMetrics();
  const metricCards = metrics.map((metric) => `
      <div class="analytics-item">
        <div class="analytics-label">${metric.title}</div>
        <div class="analytics-value">${metric.formatter ? metric.formatter(metric.primary, metric.primaryLabel) : formatNumber(metric.primary)}</div>
        <div class="analytics-caption">${metric.primaryLabel}</div>
        <div class="analytics-secondary">${metric.formatter ? metric.formatter(metric.secondary, metric.secondaryLabel) : formatNumber(metric.secondary)} · ${metric.secondaryLabel}</div>
      </div>
    `).join('');

  const activity = [
    {
      label: 'Всего заметок',
      value: formatNumber(state.notes.length),
    },
    {
      label: 'Личные записи',
      value: formatNumber(state.personalEntries.length),
    },
    {
      label: 'Напоминаний в работе',
      value: formatNumber(overview.reminders?.scheduled ?? state.reminders.length),
    },
    {
      label: 'Записей сна',
      value: formatNumber(state.sleepSessions.length),
    },
    {
      label: 'Метрик здоровья',
      value: formatNumber(state.healthMetrics.length),
    },
  ];

  const activityList = activity.map((item) => `
      <li class="analytics-bullet">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
      </li>
    `).join('');

  const updatedText = state.lastUpdated
    ? `${formatDate(state.lastUpdated)} ${state.lastUpdated.toLocaleTimeString('ru-RU')}`
    : 'ещё не обновлялось';

  return `
    <div class="card">
      <div class="section-header">
        <div>
          <h3>Ключевые показатели</h3>
          <small>Синхронизация: ${updatedText}</small>
        </div>
      </div>
      <div class="grid analytics-grid">
        ${metricCards}
      </div>
    </div>
    <div class="card">
      <div class="section-header">
        <div>
          <h3>Состояние данных</h3>
          <small>Сводка по всем разделам</small>
        </div>
      </div>
      <ul class="analytics-list">
        ${activityList}
      </ul>
    </div>
  `;
}

function renderTasksDetail() {
  const { tasks } = state;
  const total = state.overview?.tasks?.total ?? tasks.length;
  const openCount = state.overview?.tasks?.open;
  const completedCount = state.overview?.tasks?.completed;
  const content = tasks.length === 0
    ? '<div class="empty">Задачи еще не добавлены. Создай задачу через бота, и она появится здесь.</div>'
    : tasks.map((task) => `
        <div class="item">
          <strong>${task.title ?? 'Без названия'}</strong>
          <span>${task.description ?? 'Описание отсутствует'}</span>
          <div class="tags">
            <span class="tag">${task.status ?? 'new'}</span>
            ${task.priority ? `<span class="tag">${task.priority}</span>` : ''}
            ${task.deadline ? `<span class="tag">до ${formatDate(task.deadline)}</span>` : ''}
          </div>
          <span class="timestamp">Создано: ${formatDate(task.created_at)}</span>
        </div>
      `).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Задачи</h3>
        <small>${total} шт.${openCount != null ? ` · в работе: ${openCount}` : ''}${completedCount != null ? ` · готово: ${completedCount}` : ''}</small>
      </div>
      <div class="grid">${content}</div>
    </div>
  `;
}

function renderNotesDetail() {
  const { notes } = state;
  const total = state.overview?.notes?.total ?? notes.length;
  const content = notes.length === 0
    ? '<div class="empty">Заметки появятся тут после создания через ассистента.</div>'
    : notes.map((note) => `
        <div class="item">
          <strong>${note.title ?? 'Заметка'}</strong>
          <span>${note.content ? note.content.substring(0, 150) : 'Текст отсутствует'}</span>
          <span class="timestamp">Создано: ${formatDate(note.created_at)}</span>
        </div>
      `).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Заметки</h3>
        <small>${total} шт.</small>
      </div>
      <div class="grid">${content}</div>
    </div>
  `;
}

function renderFinancesDetail() {
  const { finances, financeAccounts, financeCategories, financeCategoryRules, financeView } = state;
  const summary = state.overview?.finances;

  const toolbar = `
    <div class="finance-toolbar">
      <div class="finance-tabs">
        ${['overview', 'accounts', 'categories', 'rules'].map((view) => {
          const labelMap = {
            overview: 'Операции',
            accounts: 'Счета',
            categories: 'Категории',
            rules: 'Правила',
          };
          const isActive = financeView === view;
          return `<button type="button" class="chip ${isActive ? 'active' : ''}" data-action="finance-view" data-view="${view}">${labelMap[view]}</button>`;
        }).join('')}
      </div>
      <div class="finance-actions">
        ${financeView === 'overview' ? '<button type="button" data-action="finance-add-transaction">Добавить операцию</button>' : ''}
        ${financeView === 'accounts' ? '<button type="button" data-action="finance-add-account">Добавить счёт</button>' : ''}
        ${financeView === 'categories' ? '<button type="button" data-action="finance-add-category">Добавить категорию</button>' : ''}
        ${financeView === 'rules' ? '<button type="button" data-action="finance-add-rule">Добавить правило</button>' : ''}
      </div>
    </div>
  `;

  if (financeView === 'accounts') {
    if (!financeAccounts.length) {
      return `
        ${toolbar}
        <div class="card">
          <div class="empty">${tone('accountsEmpty')}</div>
        </div>
      `;
    }

    const cards = financeAccounts.map((account) => {
      const balance = account.balance != null ? formatAmount(account.balance) : '—';
      return `
        <div class="card account-card" data-id="${account.id}">
          <div class="section-header">
            <div>
              <h3>${account.icon || '🏦'} ${account.name}</h3>
              <small>${ACCOUNT_TYPE_LABELS[account.account_type] || account.account_type || 'Счёт'}</small>
              <small>${balance}</small>
            </div>
            <div class="tags">
              <button type="button" class="secondary" data-action="finance-edit-account" data-id="${account.id}">Изменить</button>
              <button type="button" class="secondary danger" data-action="finance-delete-account" data-id="${account.id}">Удалить</button>
            </div>
          </div>
          <div class="account-meta">
            <span>Валюта: ${account.currency || 'RUB'}</span>
            ${account.is_archived ? '<span class="tag">архив</span>' : ''}
          </div>
        </div>
      `;
    }).join('');

    return `${toolbar}<div class="grid">${cards}</div>`;
  }

  if (financeView === 'categories') {
    if (!financeCategories.length) {
      return `
        ${toolbar}
        <div class="card">
          <div class="empty">${tone('categoriesEmpty')}</div>
        </div>
      `;
    }

    const cards = financeCategories.map((category) => {
      const income = category.total_income ?? 0;
      const expense = category.total_expense ?? 0;
      const balance = income - expense;
      return `
        <div class="card category-card" data-id="${category.id}">
          <div class="section-header">
            <div>
              <h3>${category.icon || '🏷️'} ${category.name}</h3>
              <small>${category.type === 'income' ? 'Доходная' : 'Расходная'} категория</small>
              <small>Баланс ${formatAmount(balance)}</small>
            </div>
            <div class="tags">
              <button type="button" class="secondary" data-action="finance-edit-category" data-id="${category.id}">Изменить</button>
              <button type="button" class="secondary" data-action="finance-purge-category" data-id="${category.id}">Очистить</button>
              <button type="button" class="secondary danger" data-action="finance-delete-category" data-id="${category.id}">Удалить</button>
            </div>
          </div>
          <div class="category-stats">
            <span class="tag green">Доходы ${formatAmount(income)}</span>
            <span class="tag red">Расходы ${formatAmount(expense)}</span>
          </div>
        </div>
      `;
    }).join('');

    return `${toolbar}<div class="grid">${cards}</div>`;
  }

  if (financeView === 'rules') {
    if (!financeCategoryRules.length) {
      return `
        ${toolbar}
        <div class="card">
          <div class="empty">${tone('rulesEmpty')}</div>
        </div>
      `;
    }

    const ruleCards = financeCategoryRules.map((rule) => {
      const category = financeCategories.find((cat) => cat.id === rule.category_id);
      const categoryLabel = category ? `${category.icon || '🏷️'} ${category.name}` : 'Категория удалена';
      const matchLabel = RULE_MATCH_TYPES.find((item) => item.value === rule.match_type)?.label ?? rule.match_type;
      return `
        <div class="card rule-card" data-id="${rule.id}">
          <div class="section-header">
            <div>
              <h3>${matchLabel}</h3>
              <small>${rule.match_pattern}</small>
              <small>Категория: ${categoryLabel}</small>
            </div>
            <div class="tags">
              <span class="tag">Доверие: ${(rule.confidence ?? 1) * 100}%</span>
              <button type="button" class="secondary" data-action="finance-edit-rule" data-id="${rule.id}">Изменить</button>
              <button type="button" class="secondary danger" data-action="finance-delete-rule" data-id="${rule.id}">Удалить</button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    return `${toolbar}<div class="grid">${ruleCards}</div>`;
  }

  const byAccount = finances.reduce((acc, tx) => {
    const key = tx.account_id || 'uncategorized';
    const bucket = acc.get(key) || [];
    bucket.push(tx);
    acc.set(key, bucket);
    return acc;
  }, new Map());

  const totals = finances.reduce((acc, tx) => {
    if (tx.type === 'income') {
      acc.income += Number(tx.amount || 0);
    } else {
      acc.expense += Number(tx.amount || 0);
    }
    return acc;
  }, { income: 0, expense: 0 });

  const balance = totals.income - totals.expense;

  const accountSections = Array.from(byAccount.entries()).map(([accountId, txs]) => {
    const account = financeAccounts.find((accItem) => accItem.id === accountId);
    const accountTitle = account ? `${account.icon || '🏦'} ${account.name}` : 'Без счёта';
    const rows = txs.map((tx) => {
      const category = financeCategories.find((cat) => cat.id === tx.category_id);
      const categoryLabel = category ? `${category.icon || '🏷️'} ${category.name}` : 'Категория не указана';
      return `
        <div class="item" data-id="${tx.id}">
          <strong>${tx.type === 'income' ? '💰 Доход' : '💸 Расход'} — ${formatAmount(tx.amount)}</strong>
          <span>${tx.description || 'Без описания'}</span>
          <div class="tags">
            <span class="tag ${tx.type === 'income' ? 'green' : 'red'}">${tx.type}</span>
            <span class="tag">${formatDateTime(tx.transaction_date)}</span>
            <span class="tag">${categoryLabel}</span>
          </div>
          <div class="item-actions">
            <button type="button" class="secondary" data-action="finance-edit-transaction" data-id="${tx.id}">Изменить</button>
            <button type="button" class="secondary danger" data-action="finance-delete-transaction" data-id="${tx.id}">Удалить</button>
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="card">
        <div class="section-header">
          <div>
            <h3>${accountTitle}</h3>
            <small>${txs.length} ${pluralize(txs.length, ['операция', 'операции', 'операций'])}</small>
          </div>
        </div>
        <div class="grid">${rows}</div>
      </div>
    `;
  }).join('');

  const summaryCard = `
    <div class="card">
      <div class="section-header">
        <h3>Операции</h3>
        <div class="tags">
          <span class="tag green">доходов: ${formatAmount(summary?.income ?? totals.income)}</span>
          <span class="tag red">расходов: ${formatAmount(summary?.expense ?? totals.expense)}</span>
          <span class="tag">баланс: ${formatAmount(summary?.balance ?? balance)}</span>
        </div>
      </div>
    </div>
  `;

  if (!finances.length) {
    return `
      ${toolbar}
      <div class="card">
        <div class="empty">${tone('financesEmpty')}</div>
      </div>
    `;
  }

  return `${toolbar}${summaryCard}${accountSections}`;
}

function renderDebtsDetail() {
  const { debts } = state;
  const overviewDebts = state.overview?.debts;
  if (!debts.length) {
    return `
      <div class="card">
        <div class="section-header">
          <h3>Долги</h3>
          <small>${formatNumber(overviewDebts?.total ?? 0)} записей</small>
        </div>
        <div class="empty">Попроси бота зафиксировать долг, и он появится здесь.</div>
      </div>
    `;
  }

  const rows = debts.map((debt) => {
    const statusLabel = debt.status === 'paid' ? '✅ закрыт' : debt.status === 'overdue' ? '⚠️ просрочен' : '⏳ активен';
    return `
      <div class="item">
        <strong>${debt.counterparty}</strong>
        <span>${statusLabel}</span>
        <div class="tags">
          <span class="tag">${debt.direction === 'owed_by_me' ? 'я должен' : 'мне должны'}</span>
          <span class="tag">${formatAmount(debt.amount)}</span>
          ${debt.due_date ? `<span class="tag">до ${formatDate(debt.due_date)}</span>` : ''}
        </div>
        ${debt.notes ? `<span>${debt.notes}</span>` : ''}
      </div>
    `;
  }).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Долги</h3>
        <small>${formatNumber(overviewDebts?.total ?? debts.length)} записей · открыто: ${formatNumber(overviewDebts?.openCount ?? debts.length)}</small>
      </div>
      <div class="grid">${rows}</div>
    </div>
  `;
}

function renderRemindersDetail() {
  const { reminders } = state;
  const overviewReminders = state.overview?.reminders;
  if (!reminders.length) {
    const nextText = overviewReminders?.next ? `· ближайшее: ${formatDateTime(overviewReminders.next)}` : '';
    return `
      <div class="card">
        <div class="section-header">
          <h3>Напоминания</h3>
          <small>${formatNumber(overviewReminders?.total ?? 0)} всего ${nextText}</small>
        </div>
        <div class="empty">Скажи боту «Напомни мне...», и здесь появится список предстоящих уведомлений.</div>
      </div>
    `;
  }

  const rows = reminders.map((reminder) => `
    <div class="item">
      <strong>${reminder.title}</strong>
      <span class="timestamp">${formatDateTime(reminder.reminder_time)}</span>
      <div class="tags">
        <span class="tag ${reminder.status === 'scheduled' ? 'green' : 'secondary'}">${reminder.status}</span>
        <span class="tag">${reminder.timezone}</span>
      </div>
      ${reminder.recurrence_rule ? `<small>Повторение: ${reminder.recurrence_rule}</small>` : ''}
    </div>
  `).join('');

  const nextText = overviewReminders?.next ? `Ближайшее: ${formatDateTime(overviewReminders.next)}` : '';

  return `
    <div class="card">
      <div class="section-header">
        <h3>Напоминания</h3>
        <small>${formatNumber(overviewReminders?.scheduled ?? reminders.length)} активных · ${nextText}</small>
      </div>
      <div class="grid">${rows}</div>
    </div>
  `;
}

function renderOverview() {
  const { overview } = state;
  if (!overview) {
    return '';
  }

  const cards = [
    {
      title: 'Задачи',
      primary: overview.tasks?.total ?? 0,
      primaryLabel: 'всего',
      secondary: overview.tasks?.open,
      secondaryLabel: 'в работе',
      icon: '🗂️',
    },
    {
      title: 'Финансы',
      primary: overview.finances?.balance ?? 0,
      primaryLabel: 'баланс',
      secondary: overview.finances?.income ?? 0,
      secondaryLabel: 'доходы',
      icon: '💰',
      formatter: (value) => formatAmount(value),
    },
    {
      title: 'Долги',
      primary: overview.debts?.openCount ?? 0,
      primaryLabel: 'открыто',
      secondary: overview.debts?.openAmount ?? 0,
      secondaryLabel: '₽ в работе',
      icon: '📉',
      formatter: (value, label) => label.includes('₽') ? formatAmount(value) : formatNumber(value),
    },
    {
      title: 'Напоминания',
      primary: overview.reminders?.scheduled ?? 0,
      primaryLabel: 'активных',
      secondary: overview.reminders?.next ? formatDateTime(overview.reminders.next) : '—',
      secondaryLabel: 'ближайшее',
      icon: '⏰',
      formatter: (value) => value,
    },
    {
      title: 'Заметки',
      primary: overview.notes?.total ?? 0,
      primaryLabel: 'всего',
      secondary: overview.personal?.total ?? 0,
      secondaryLabel: 'личных записей',
      icon: '📝',
    },
  ];

  const items = cards.map((card) => {
    const formatter = card.formatter || ((value) => formatNumber(value));
    return `
      <div class="overview-item">
        <div class="overview-icon">${card.icon}</div>
        <div class="overview-content">
          <div class="overview-title">${card.title}</div>
          <div class="overview-metric">${formatter(card.primary, card.primaryLabel)} <span>${card.primaryLabel}</span></div>
          <div class="overview-secondary">${formatter(card.secondary, card.secondaryLabel)} <span>${card.secondaryLabel}</span></div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="card overview">
      <div class="section-header">
        <h3>Сводка</h3>
        <small>Единое состояние по данным MISIX</small>
      </div>
      <div class="overview-grid">${items}</div>
    </div>
  `;
}

function renderSleepDetail() {
  const { sleepSessions } = state;
  if (sleepSessions.length === 0) {
    return `
      <div class="card">
        <div class="section-header">
          <h3>Сон</h3>
          <small>0 сессий</small>
        </div>
        <div class="empty">Запусти сон в Телеграме, и статистика появится здесь.</div>
      </div>
    `;
  }

  const sessions = sleepSessions.map((session) => {
    const totalSleep = Number(session.total_sleep_seconds || 0);
    const totalPause = Number(session.total_pause_seconds || 0);
    const hours = Math.floor(totalSleep / 3600);
    const minutes = Math.floor((totalSleep % 3600) / 60);
    const pauseMinutes = Math.round(totalPause / 60);

    return `
      <div class="item">
        <strong>Статус: ${session.status}</strong>
        <span>Сон: ${hours} ч ${minutes} мин</span>
        <span>Пауза: ${pauseMinutes} мин</span>
        <span class="timestamp">${formatDate(session.created_at)}</span>
      </div>
    `;
  }).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Сон</h3>
        <small>${sleepSessions.length} последних сессий</small>
      </div>
      <div class="grid">${sessions}</div>
    </div>
  `;
}

function renderHealthDetail() {
  const { healthMetrics, healthFilterType, healthFilterPeriod } = state;
  const availableTypes = getUniqueMetricTypes(healthMetrics);
  const filteredMetrics = filterHealthMetrics(healthMetrics);
  const summary = computeHealthSummary(filteredMetrics);
  const sparkline = buildSparklineSvg(filteredMetrics);

  const items = filteredMetrics
    .slice()
    .reverse()
    .map((metric) => `
      <div class="item">
        <strong>${metric.metric_type ?? 'Показатель'} — ${metric.metric_value ?? '?'} ${metric.unit ?? ''}</strong>
        <span>${metric.note ?? 'Без заметок'}</span>
        <span class="timestamp">Записано: ${formatDateTime(metric.recorded_at)}</span>
      </div>
    `).join('');

  const hasData = healthMetrics.length > 0;
  const hasFilteredData = filteredMetrics.length > 0;

  return `
    <div class="card">
      <div class="section-header">
        <h3>Здоровье</h3>
        <small>${hasData ? `${healthMetrics.length} записей` : 'Нет записей'}</small>
      </div>
      <div class="health-toolbar">
        <label>
          Тип показателя
          <select id="health-filter-type">
            <option value="all" ${healthFilterType === 'all' ? 'selected' : ''}>Все</option>
            ${availableTypes.map((type) => `<option value="${type}" ${healthFilterType === type ? 'selected' : ''}>${type}</option>`).join('')}
          </select>
        </label>
        <label>
          Период
          <select id="health-filter-period">
            <option value="7" ${healthFilterPeriod === '7' ? 'selected' : ''}>7 дней</option>
            <option value="30" ${healthFilterPeriod === '30' ? 'selected' : ''}>30 дней</option>
            <option value="90" ${healthFilterPeriod === '90' ? 'selected' : ''}>90 дней</option>
            <option value="365" ${healthFilterPeriod === '365' ? 'selected' : ''}>1 год</option>
          </select>
        </label>
      </div>
      ${summary ? `
        <div class="health-summary">
          <span><strong>Последнее:</strong> ${summary.latest.toFixed(2)}</span>
          <span><strong>Ср. значение:</strong> ${summary.avg.toFixed(2)}</span>
          <span><strong>Мин:</strong> ${summary.min.toFixed(2)}</span>
          <span><strong>Макс:</strong> ${summary.max.toFixed(2)}</span>
          <span><strong>Δ:</strong> ${summary.delta >= 0 ? '+' : ''}${summary.delta.toFixed(2)}</span>
        </div>
      ` : ''}
      ${sparkline ? `<div class="sparkline-wrapper">${sparkline}</div>` : ''}
      ${hasFilteredData ? `<div class="grid">${items}</div>` : `<div class="empty">Нет данных за выбранный период. Попробуй другой фильтр.</div>`}
      ${!hasData ? '<div class="empty">Фиксируй показатели через бота, и они появятся здесь.</div>' : ''}
    </div>
  `;
}

function renderPersonalDataDetail() {
  const { personalEntries } = state;
  if (personalEntries.length === 0) {
    return `
      <div class="card">
        <div class="section-header">
          <h3>Личные данные</h3>
          <small>0 записей</small>
        </div>
        <div class="empty">Спроси бота сохранить контакты или логины, и они появятся здесь (чувствительные данные скрыты).</div>
      </div>
    `;
  }

  const entries = personalEntries.map((entry) => {
    const details = [
      entry.contact_name ? `<span>Контакт: ${entry.contact_name}</span>` : '',
      entry.login_username ? `<span>Логин: ${formatSensitive(entry.login_username)}</span>` : '',
      entry.login_password ? `<span>Пароль: ${formatSensitive(entry.login_password)}</span>` : '',
      entry.contact_phone ? `<span>Телефон: ${formatSensitive(entry.contact_phone)}</span>` : '',
      entry.contact_email ? `<span>Email: ${formatSensitive(entry.contact_email)}</span>` : '',
      entry.document_number ? `<span>Документ: ${formatSensitive(entry.document_number)}</span>` : '',
      entry.document_expiry ? `<span>Срок: ${formatDate(entry.document_expiry)}</span>` : '',
      entry.notes ? `<span>${entry.notes}</span>` : '',
    ].filter(Boolean).join('');

    const tags = Array.isArray(entry.tags) && entry.tags.length
      ? entry.tags.map((tag) => `<span class="tag">${tag}</span>`).join('')
      : '';

    return `
      <div class="item">
        <strong>${entry.title ?? 'Запись'}</strong>
        <span>Тип: ${entry.data_type ?? 'unknown'} ${entry.is_favorite ? '⭐' : ''}</span>
        <div class="details">${details || '<span>Подробности отсутствуют.</span>'}</div>
        <div class="tags">${tags}</div>
        <span class="timestamp">Добавлено: ${formatDateTime(entry.created_at)}</span>
      </div>
    `;
  }).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Личные данные</h3>
        <small>${personalEntries.length} записей</small>
      </div>
      <div class="grid">${entries}</div>
    </div>
  `;
}

function renderSummaryCards() {
  const cards = DASHBOARD_SECTIONS.map((section) => {
    const summary = section.summary();
    return `
      <div class="card overview summary-card" data-section="${section.key}">
        <div class="summary-heading">
          <div class="summary-title">
            <span class="summary-icon">${section.icon}</span>
            <div>
              <h3>${section.title}</h3>
              <small>${summary.primary}</small>
            </div>
          </div>
          <button type="button" class="secondary summary-open" data-action="open-detail" data-section="${section.key}">Открыть</button>
        </div>
        <p class="summary-secondary">${summary.secondary}</p>
      </div>
    `;
  }).join('');

  return `
    <div class="grid summary-grid">
      ${cards}
    </div>
  `;
}

function renderDashboard() {
  const overlay = state.passwordConfigured && !state.unlocked ? renderLockOverlay() : '';
  const content = state.view === 'detail' ? renderDetailView() : renderSummaryCards();
  const modal = state.modal ? renderModal(state.modal) : '';
  return `
    ${renderToolbar()}
    ${content}
    ${renderFooter()}
    ${modal}
    ${overlay}
  `;
}

function renderLockOverlay() {
  return `
    <div class="modal-backdrop lock">
      <div class="modal bounce-in" id="unlock-modal">
        <h3>Введите PIN</h3>
        <p>Для доступа к дашборду нужно подтвердить код</p>
        ${renderPinDots(state.pinEntry)}
        ${state.pinError ? `<div class="error">${state.pinError}</div>` : ''}
        ${renderNumpad()}
        <div class="modal-actions">
          <button type="button" class="link" id="unlock-forgot">Забыли PIN?</button>
        </div>
      </div>
    </div>
  `;
}

function renderFooter() {
  return `
    <div class="footer">
      <button type="button" class="settings-btn" id="open-settings">⚙️ Настройки</button>
    </div>
  `;
}

function renderPinDots(entry) {
  return `
    <div class="pin-dots">
      ${entry.map((digit, index) => `<div class="dot ${digit ? 'filled' : ''}" data-index="${index}"></div>`).join('')}
    </div>
  `;
}

function renderNumpad() {
  const keys = ['1','2','3','4','5','6','7','8','9','back','0','ok'];
  return `
    <div class="numpad">
      ${keys.map((key) => {
        if (key === 'back') {
          return `<button type="button" class="numpad-key" data-key="back">⌫</button>`;
        }
        if (key === 'ok') {
          return `<button type="button" class="numpad-key confirm" data-key="ok">OK</button>`;
        }
        return `<button type="button" class="numpad-key" data-key="${key}">${key}</button>`;
      }).join('')}
    </div>
  `;
}

function renderPasswordModalContent() {
  const { settingsMode, pinEntry, pinError, securityQuestion, pinStep, passwordConfigured } = state;
  const stepText = {
    set: {
      enter: 'Придумайте PIN из 4 цифр',
      confirm: 'Повторите PIN',
      question: 'Придумайте секретный вопрос',
      answer: 'Ответ на секретный вопрос'
    },
    change: {
      enter: 'Введите текущий PIN',
      new: 'Новый PIN (4 цифры)',
      confirm: 'Повторите новый PIN'
    },
    delete: {
      question: `Вопрос: ${securityQuestion ?? ''}`,
      answer: 'Введите ответ'
    },
    wipe: {
      question: `Вопрос: ${securityQuestion ?? ''}`,
      answer: 'Введите ответ для удаления данных'
    }
  };

  const currentSteps = stepText[settingsMode] || {};
  const titleMap = {
    set: 'Установка PIN',
    change: 'Изменение PIN',
    delete: 'Удаление PIN',
    wipe: 'Удаление данных'
  };

  if (settingsMode === 'set') {
    if (pinStep === 'question' || pinStep === 'answer') {
      return `
        <h3>${titleMap[settingsMode]}</h3>
        <p>${currentSteps[pinStep]}</p>
        <input type="text" id="security-${pinStep}" class="input" placeholder="${pinStep === 'question' ? 'Например: имя первого учителя' : 'Ответ'}" />
        ${pinError ? `<div class="error">${pinError}</div>` : ''}
        <div class="modal-actions">
          <button type="button" class="secondary" id="cancel-settings">Отмена</button>
          <button type="button" id="confirm-security">Продолжить</button>
        </div>
      `;
    }
  }

  if (settingsMode === 'delete' || settingsMode === 'wipe') {
    return `
      <h3>${titleMap[settingsMode]}</h3>
      <p>${currentSteps.question}</p>
      <input type="text" id="security-answer" class="input" placeholder="Ответ" />
      ${pinError ? `<div class="error">${pinError}</div>` : ''}
      <div class="modal-actions">
        <button type="button" class="secondary" id="cancel-settings">Отмена</button>
        <button type="button" id="confirm-security">Подтвердить</button>
      </div>
    `;
  }

  return `
    <h3>${titleMap[settingsMode] ?? 'PIN'}</h3>
    <p>${currentSteps[pinStep] ?? ''}</p>
    ${renderPinDots(pinEntry)}
    ${pinError ? `<div class="error">${pinError}</div>` : ''}
    ${renderNumpad()}
    <div class="modal-actions">
      ${settingsMode === 'set' || settingsMode === 'change' ? `<button type="button" class="link" id="cancel-settings">Отмена</button>` : ''}
      ${settingsMode === 'set' && passwordConfigured ? '<button type="button" class="link" id="forgot-pin">Забыли PIN?</button>' : ''}
    </div>
  `;
}

function renderSettingsView() {
  const { passwordConfigured } = state;
  return `
    <div class="card settings-card fade-in">
      <div class="section-header">
        <div>
          <h3>Настройки безопасности</h3>
          <small>PIN-защита доступа к MISIX</small>
        </div>
        <button type="button" class="secondary" id="close-settings">Назад</button>
      </div>
      <div class="settings-list">
        ${!passwordConfigured ? `
          <button type="button" class="settings-item" data-action="set-password">
            <div>
              <strong>Установить PIN</strong>
              <span>Создайте четырёхзначный код и секретный вопрос</span>
            </div>
            <span class="arrow">›</span>
          </button>
        ` : ''}
        ${passwordConfigured ? `
          <button type="button" class="settings-item" data-action="change-password">
            <div>
              <strong>Изменить PIN</strong>
              <span>Введите текущий код и установите новый</span>
            </div>
            <span class="arrow">›</span>
          </button>
          <button type="button" class="settings-item" data-action="delete-password">
            <div>
              <strong>Удалить PIN</strong>
              <span>Ответьте на секретный вопрос, чтобы отключить PIN</span>
            </div>
            <span class="arrow danger">›</span>
          </button>
          <button type="button" class="settings-item danger" data-action="wipe-data">
            <div>
              <strong>Удалить всю информацию</strong>
              <span>Потребуется подтвердить секретный ответ</span>
            </div>
            <span class="arrow danger">›</span>
          </button>
        ` : ''}
      </div>
    </div>
    ${state.showSettingsModal ? `
      <div class="modal-backdrop">
        <div class="modal bounce-in" id="settings-modal">
          ${renderPasswordModalContent()}
        </div>
      </div>
    ` : ''}
  `;
}

function renderRoot() {
  const root = document.getElementById('app');
  if (!root) return;

  if (!state.userId) {
    root.innerHTML = renderLogin();
    const tgButton = document.getElementById('tg-login');
    if (tgButton) tgButton.addEventListener('click', tryTelegramLogin);
    const devButton = document.getElementById('dev-login');
    if (devButton) devButton.addEventListener('click', tryDevLogin);
    initSettingsListeners();
    return;
  }

  if (state.view === 'settings') {
    root.innerHTML = `
      ${renderToolbar()}
      ${renderSettingsView()}
    `;
  } else {
    root.innerHTML = renderDashboard();
  }

  initDashboardListeners();
  initSettingsListeners();
  initLockListeners();
}

function initDashboardListeners() {
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) refreshBtn.addEventListener('click', loadData);

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);

  document.querySelectorAll('[data-action="open-detail"]').forEach((button) => {
    button.addEventListener('click', (event) => {
      const section = event.currentTarget.getAttribute('data-section');
      if (!section) return;
      setState({ view: 'detail', detailSection: section });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  document.querySelectorAll('[data-action="back-to-summary"]').forEach((button) => {
    button.addEventListener('click', () => {
      setState({ view: 'summary', detailSection: null });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  const openSettingsBtn = document.getElementById('open-settings');
  if (openSettingsBtn) {
    openSettingsBtn.addEventListener('click', () => {
      setState({ view: 'settings' });
    });
  }

  const healthTypeSelect = document.getElementById('health-filter-type');
  if (healthTypeSelect) {
    healthTypeSelect.addEventListener('change', (event) => {
      setState({ healthFilterType: event.target.value });
    });
  }

  const healthPeriodSelect = document.getElementById('health-filter-period');
  if (healthPeriodSelect) {
    healthPeriodSelect.addEventListener('change', (event) => {
      setState({ healthFilterPeriod: event.target.value });
    });
  }
}

function initSettingsListeners() {
  const closeSettings = document.getElementById('close-settings');
  if (closeSettings) {
    closeSettings.addEventListener('click', () => {
      setState({ view: 'summary', showSettingsModal: false, settingsMode: null });
      resetPinEntry('enter');
    });
  }

  document.querySelectorAll('.settings-item').forEach((item) => {
    item.addEventListener('click', (event) => {
      const target = event.currentTarget;
      const action = target.getAttribute('data-action');
      handleSettingsAction(action);
    });
  });

  const cancelSettings = document.getElementById('cancel-settings');
  if (cancelSettings) {
    cancelSettings.addEventListener('click', () => {
      setState({ showSettingsModal: false, settingsMode: null });
      resetPinEntry('enter');
    });
  }

  const confirmSecurity = document.getElementById('confirm-security');
  if (confirmSecurity) {
    confirmSecurity.addEventListener('click', handleSecurityConfirmation);
  }

  const forgotPin = document.getElementById('forgot-pin');
  if (forgotPin) {
    forgotPin.addEventListener('click', () => {
      setState({ settingsMode: 'delete', showSettingsModal: true, pinStep: 'question', pinError: null });
    });
  }

  document.querySelectorAll('#settings-modal .numpad-key').forEach((key) => {
    key.addEventListener('click', () => handleNumpadInput(key.getAttribute('data-key')));
  });

  const securityQuestionInput = document.getElementById('security-question');
  if (securityQuestionInput) {
    securityQuestionInput.value = state.securityQuestion || '';
  }

  const securityAnswerInput = document.getElementById('security-answer');
  if (securityAnswerInput && (state.settingsMode === 'set' && state.pinStep === 'answer')) {
    securityAnswerInput.value = state.securityAnswer || '';
  }
}

function initLockListeners() {
  if (!(state.passwordConfigured && !state.unlocked)) {
    return;
  }

  document.querySelectorAll('#unlock-modal .numpad-key').forEach((key) => {
    key.addEventListener('click', () => handleNumpadInput(key.getAttribute('data-key')));
  });

  const forgotBtn = document.getElementById('unlock-forgot');
  if (forgotBtn) {
    forgotBtn.addEventListener('click', () => {
      if (!state.securityQuestion) {
        alert('Секретный вопрос не настроен. Обратитесь в поддержку.');
        return;
      }
      setState({
        view: 'settings',
        showSettingsModal: true,
        settingsMode: 'delete',
        pinStep: 'question',
        pinError: null,
      });
    });
  }
}

function hashPin(pin) {
  return btoa(pin.split('').reverse().join(''));
}

function verifyPin(pin, hash) {
  return hashPin(pin) === hash;
}

function handleSettingsAction(action) {
  switch (action) {
    case 'set-password':
      resetPinEntry('enter');
      setState({ showSettingsModal: true, settingsMode: 'set', pinStep: 'enter', pinError: null });
      break;
    case 'change-password':
      resetPinEntry('enter');
      setState({ showSettingsModal: true, settingsMode: 'change', pinStep: 'enter', pinError: null });
      break;
    case 'delete-password':
      setState({ showSettingsModal: true, settingsMode: 'delete', pinStep: 'question', pinError: null });
      break;
    case 'wipe-data':
      setState({ showSettingsModal: true, settingsMode: 'wipe', pinStep: 'question', pinError: null });
      break;
    default:
      break;
  }
}

function handleNumpadInput(key) {
  const currentEntry = [...state.pinEntry];
  if (key === 'back') {
    for (let i = currentEntry.length - 1; i >= 0; i -= 1) {
      if (currentEntry[i]) {
        currentEntry[i] = '';
        break;
      }
    }
    setState({ pinEntry: currentEntry, pinError: null });
    return;
  }

  if (key === 'ok') {
    processPinEntry();
    return;
  }

  if (!/^[0-9]$/.test(key)) {
    return;
  }

  for (let i = 0; i < currentEntry.length; i += 1) {
    if (!currentEntry[i]) {
      currentEntry[i] = key;
      break;
    }
  }
  setState({ pinEntry: currentEntry });
  if (currentEntry.every((value) => value)) {
    processPinEntry();
  }
}

function processPinEntry() {
  const pin = state.pinEntry.join('');
  if (pin.length < 4) {
    setState({ pinError: 'Нужно 4 цифры' });
    return;
  }

  if (state.passwordConfigured && !state.unlocked && state.settingsMode === null) {
    if (!state.passwordHash) {
      setState({ pinError: 'PIN не настроен' });
      return;
    }
    if (!verifyPin(pin, state.passwordHash)) {
      resetPinEntry('enter');
      setState({ pinError: 'Неверный PIN' });
      return;
    }
    setState({ unlocked: true, pinError: null, pinEntry: ['', '', '', ''] });
    loadData();
    return;
  }

  if (state.settingsMode === 'set') {
    if (state.pinStep === 'enter') {
      state.tmpPin = pin;
      resetPinEntry('confirm');
      render();
      return;
    }
    if (state.pinStep === 'confirm') {
      if (pin !== state.tmpPin) {
        state.tmpPin = null;
        resetPinEntry('enter');
        setState({ pinError: 'PIN не совпадает, попробуй снова' });
        return;
      }
      state.passwordHash = hashPin(pin);
      resetPinEntry('question');
      setState({ pinError: null });
      return;
    }
  }

  if (state.settingsMode === 'change') {
    if (state.pinStep === 'enter') {
      if (!verifyPin(pin, state.passwordHash)) {
        resetPinEntry('enter');
        setState({ pinError: 'Неверный текущий PIN' });
        return;
      }
      resetPinEntry('new');
      setState({ pinError: null });
      return;
    }
    if (state.pinStep === 'new') {
      state.tmpPin = pin;
      resetPinEntry('confirm');
      setState({ pinError: null });
      return;
    }
    if (state.pinStep === 'confirm') {
      if (pin !== state.tmpPin) {
        resetPinEntry('new');
        setState({ pinError: 'PIN не совпадает' });
        return;
      }
      state.passwordHash = hashPin(pin);
      state.tmpPin = null;
      persistSecurityToStorage();
      finalizeSettingsChange('PIN обновлён');
      return;
    }
  }

  if (state.settingsMode === 'delete') {
    // Should not reach here via PIN
    return;
  }
}

function handleSecurityConfirmation() {
  if (state.settingsMode === 'set') {
    if (state.pinStep === 'question') {
      const questionInput = document.getElementById('security-question');
      const question = questionInput?.value.trim();
      if (!question) {
        setState({ pinError: 'Введите вопрос' });
        return;
      }
      setState({ securityQuestion: question });
      resetPinEntry('answer');
      render();
      return;
    }
    if (state.pinStep === 'answer') {
      const answerInput = document.getElementById('security-answer');
      const answer = answerInput?.value.trim();
      if (!answer) {
        setState({ pinError: 'Введите ответ' });
        return;
      }
      setState({ securityAnswer: answer, passwordConfigured: true, showSettingsModal: false, settingsMode: null, pinError: null });
      resetPinEntry('enter');
      persistSecurityToStorage();
      alert('PIN установлен — при входе появится экран ввода кода.');
      render();
      return;
    }
  }

  if (state.settingsMode === 'delete' || state.settingsMode === 'wipe') {
    const answerInput = document.getElementById('security-answer');
    const answer = answerInput?.value.trim();
    if (!answer) {
      setState({ pinError: 'Введите ответ' });
      return;
    }
    if (answer !== state.securityAnswer) {
      setState({ pinError: 'Ответ не совпадает' });
      return;
    }
    if (state.settingsMode === 'delete') {
      resetSecuritySettings();
      clearSecurityFromStorage();
      setState({ showSettingsModal: false, settingsMode: null });
      resetPinEntry('enter');
      alert('PIN удалён.');
      render();
    } else {
      // wipe data
      wipeUserData();
    }
  }
}

function finalizeSettingsChange(message) {
  setState({ showSettingsModal: false, settingsMode: null, pinError: null });
  resetPinEntry('enter');
  alert(message);
  render();
}

function wipeUserData() {
  // Here we simply reset state (server-side wipe should be separate endpoint)
  resetSecuritySettings();
  clearSecurityFromStorage();
  setState({
    overview: null,
    tasks: [],
    notes: [],
    finances: [],
    debts: [],
    reminders: [],
    sleepSessions: [],
    healthMetrics: [],
    personalEntries: [],
    messages: [],
    showSettingsModal: false,
  });
  resetPinEntry('enter');
  alert('Все локальные данные очищены (серверные — отдельно через админа).');
  render();
}

function render() {
  renderRoot();
}

function tryTelegramLogin() {
  if (!isTelegramWebApp()) {
    alert('Этот способ работает только из Telegram WebApp.');
    return;
  }

  const tg = window.Telegram.WebApp;
  const user = tg.initDataUnsafe?.user;
  if (!user) {
    alert('Не удалось получить данные пользователя из Telegram.');
    return;
  }

  const telegramId = user.id;

  // Запрашиваем привязку Telegram ID → user_id в БД
  setState({ loading: true, error: null });
  supabaseClient
    .from('users')
    .select('id')
    .eq('telegram_id', telegramId)
    .limit(1)
    .single()
    .then(({ data, error }) => {
      if (error || !data) {
        throw error || new Error('Пользователь не найден в базе.');
      }
      setState({ userId: data.id, userLabel: `${user.first_name || ''} ${user.last_name || ''}`.trim() });
      loadData();
    })
    .catch((err) => {
      console.error('Telegram login failed', err);
      setState({ loading: false, error: 'Не удалось найти пользователя в базе. Напиши боту, чтобы он создал запись.' });
    });
}

function tryDevLogin() {
  const password = window.prompt('Введите пароль для режима разработчика');
  if (password === null) {
    return;
  }

  if (password.trim() !== DEV_MODE_PASSWORD) {
    alert('Неверный пароль.');
    return;
  }

  if (!supabaseClient) {
    initSupabase();
  }

  setState({ loading: true, error: null });

  supabaseClient
    .from('users')
    .select('id, full_name, username')
    .eq('telegram_id', DEV_MODE_PROFILE.telegramId)
    .limit(1)
    .single()
    .then(({ data, error }) => {
      if (error || !data) {
        throw error || new Error('Пользователь не найден в базе.');
      }

      const userData = {
        ...data,
        username: data.username || DEV_MODE_PROFILE.username,
        full_name: data.full_name || DEV_MODE_PROFILE.fullName,
        first_name: DEV_MODE_PROFILE.fullName,
      };

      const displayName = formatDisplayName('', userData, DEV_MODE_PROFILE.telegramId);

      setState({
        userId: data.id,
        userLabel: displayName,
        loading: false,
        error: null,
      });

      loadData();
    })
    .catch((err) => {
      console.error('Developer mode login failed', err);
      const reason = err instanceof Error ? err.message : JSON.stringify(err);
      setState({
        loading: false,
        error: `Режим разработчика недоступен: ${reason}`,
      });
    });
}

window.addEventListener('DOMContentLoaded', () => {
  initSupabase();
  render();

  // Автологин через Telegram Web App (если открыто внутри клиента)
  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    const user = tg.initDataUnsafe?.user;
    if (user) {
      const telegramId = user.id;
      supabaseClient
        .from('users')
        .select('id')
        .eq('telegram_id', telegramId)
        .limit(1)
        .single()
        .then(({ data }) => {
          if (data?.id) {
            setState({ userId: data.id, userLabel: `${user.first_name || ''} ${user.last_name || ''}`.trim() });
            loadData();
          }
        })
        .catch(() => {
          // тихо игнорируем – пользователь просто увидит форму логина
        });
    }
  }
});
