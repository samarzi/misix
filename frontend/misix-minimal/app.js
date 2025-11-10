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

const state = {
  userId: null,
  userLabel: null,
  loading: false,
  error: null,
  view: 'dashboard',
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
  healthFilterType: 'all',
  healthFilterPeriod: '30',
  lastUpdated: null,
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
    view: 'dashboard',
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
  const name = state.userLabel ? state.userLabel : state.userId;
  const subtitle = state.lastUpdated
    ? `Обновлено ${formatDate(state.lastUpdated)} ${state.lastUpdated.toLocaleTimeString('ru-RU')}`
    : 'Данные появятся после синхронизации';

  return `
    <div class="card">
      <div class="section-header">
        <div>
          <h2 class="glow">Привет, ${name || 'друг'} 👋</h2>
          <small>${subtitle}</small>
        </div>
        <div class="toolbar">
          <button type="button" id="refresh-btn">Обновить</button>
          <button type="button" class="secondary" id="logout-btn">Выйти</button>
        </div>
      </div>
      <div class="notice${state.loading ? '' : ' hidden'}">Обновляю данные...</div>
      ${state.error ? `<div class="notice error">${state.error}</div>` : ''}
    </div>
  `;
}

function renderTasks() {
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

function renderNotes() {
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

function renderFinances() {
  const { finances } = state;
  const summary = state.overview?.finances;
  if (finances.length === 0) {
    return `
      <div class="card">
        <div class="section-header">
          <h3>Финансы</h3>
          <small>0 записей</small>
        </div>
        <div class="empty">Когда добавишь расходы или доходы через бота, они появятся здесь.</div>
      </div>
    `;
  }

  const totalIncome = finances
    .filter((tx) => tx.type === 'income')
    .reduce((acc, tx) => acc + Number(tx.amount || 0), 0);
  const totalExpense = finances
    .filter((tx) => tx.type === 'expense')
    .reduce((acc, tx) => acc + Number(tx.amount || 0), 0);

  const rows = finances.map((tx) => `
    <div class="item">
      <strong>${tx.type === 'income' ? '💰 Доход' : '💸 Расход'} — ${formatAmount(tx.amount)}</strong>
      <span>${tx.description || 'Без описания'}</span>
      <div class="tags">
        <span class="tag ${tx.type === 'income' ? 'green' : 'red'}">${tx.type}</span>
        <span class="tag">${formatDate(tx.transaction_date)}</span>
      </div>
    </div>
  `).join('');

  return `
    <div class="card">
      <div class="section-header">
        <h3>Финансы</h3>
        <div class="tags">
          <span class="tag green">доходов: ${formatAmount(summary?.income ?? totalIncome)}</span>
          <span class="tag red">расходов: ${formatAmount(summary?.expense ?? totalExpense)}</span>
          <span class="tag">баланс: ${formatAmount(summary?.balance ?? (totalIncome - totalExpense))}</span>
        </div>
      </div>
      <div class="grid">${rows}</div>
    </div>
  `;
}

function renderDebts() {
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

function renderReminders() {
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

function renderSleep() {
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

function renderHealth() {
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

function renderPersonalData() {
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

function renderDashboard() {
  const overlay = state.passwordConfigured && !state.unlocked ? renderLockOverlay() : '';
  return `
    ${renderToolbar()}
    ${renderOverview()}
    ${renderTasks()}
    ${renderNotes()}
    ${renderFinances()}
    ${renderDebts()}
    ${renderReminders()}
    ${renderSleep()}
    ${renderHealth()}
    ${renderPersonalData()}
    ${renderFooter()}
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
      setState({ view: 'dashboard', showSettingsModal: false, settingsMode: null });
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
