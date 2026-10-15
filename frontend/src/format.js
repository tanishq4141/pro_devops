const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
export const money = (v) => inr.format(Number(v || 0));
export const number = (v) => new Intl.NumberFormat('en-IN').format(Number(v || 0));
export const STATUS_LABEL = { IN_STOCK: 'In stock', LOW_STOCK: 'Low stock', OUT_OF_STOCK: 'Out of stock' };

export function timeAgo(iso) {
  const seconds = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  const units = [['day', 86400], ['hr', 3600], ['min', 60]];
  for (const [label, size] of units) {
    if (seconds >= size) {
      const n = Math.floor(seconds / size);
      return `${n} ${label}${n > 1 && label !== 'min' && label !== 'hr' ? 's' : ''} ago`;
    }
  }
  return 'just now';
}
