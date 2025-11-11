export const formatAmount = (value: number | null | undefined, currency = 'RUB') => {
  if (value == null) return '0 ₽';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatNumber = (value: number | null | undefined) => {
  if (value == null) return '0';
  return new Intl.NumberFormat('ru-RU').format(value);
};

export const formatDateTime = (value: string | number | Date | null | undefined) => {
  if (!value) return '—';
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleString('ru-RU');
};

export const formatDate = (value: string | number | Date | null | undefined) => {
  if (!value) return '—';
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleDateString('ru-RU');
};
