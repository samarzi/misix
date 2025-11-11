import type { ToneStyle } from '../config';
import type { DashboardOverview } from '../api/types';

type ToneMessages = {
  greeting: (overview?: DashboardOverview | null) => string;
  empty: (section: string) => { title: string; description: string };
};

const formatNumber = (value?: number | null) => {
  if (value == null) return '0';
  return new Intl.NumberFormat('ru-RU').format(value);
};

const formatAmount = (value?: number | null) => {
  if (value == null) return '0 ₽';
  const formatter = new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  });
  return formatter.format(value);
};

const toneMap: Record<ToneStyle, ToneMessages> = {
  neutral: {
    greeting: (overview) => {
      const tasks = overview?.tasks?.open ?? 0;
      return tasks > 0
        ? `У тебя ${tasks} незавершенных задач. Продолжим работу.`
        : 'Все спокойно. Готов продолжать, когда ты будешь готов.';
    },
    empty: (section) => ({
      title: 'Пока пусто',
      description: `Раздел «${section}» пока не содержит данных. Добавь новую запись, чтобы начать.`
    }),
  },
  teasing: {
    greeting: (overview) => {
      const completed = overview?.tasks?.completed ?? 0;
      return completed > 0
        ? `Ну давай, герой. ${completed} задач уже готово, еще пара и можно отдыхать.`
        : 'Тишина? Это не про тебя. Давай добавим дел.';
    },
    empty: (section) => ({
      title: 'Эй, тут пусто!',
      description: `Раздел «${section}» выглядит как пустой холодильник ночью. Заполним?`
    }),
  },
  business: {
    greeting: (overview) => {
      const balance = overview?.finances?.balance;
      return `Баланс ${formatAmount(balance)}. Время планировать следующие действия.`;
    },
    empty: (section) => ({
      title: 'Нет данных',
      description: `В разделе «${section}» пока нет записей. Добавь первую, чтобы увидеть аналитику.`
    }),
  },
};

export const getToneGreeting = (tone: ToneStyle, overview?: DashboardOverview | null) => {
  return toneMap[tone]?.greeting(overview) ?? toneMap.teasing.greeting(overview);
};

export const getEmptyStateMessage = (tone: ToneStyle, section: string) => {
  return toneMap[tone]?.empty(section) ?? toneMap.teasing.empty(section);
};

export const formatMetric = (value: number, unit?: string) => {
  const formatted = formatNumber(value);
  return unit ? `${formatted} ${unit}` : formatted;
};

export const formatCurrency = (value: number, currency = 'RUB') => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);
};
