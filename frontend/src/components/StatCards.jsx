import { money, number } from '../format.js';

function Stat({ label, value, hint, tone = '' }) {
  return (
    <div className={`stat ${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
      <span>{hint}</span>
    </div>
  );
}

export default function StatCards({ stats }) {
  return (
    <section className="stats">
      <Stat label="Products" value={number(stats.totalProducts)} hint={`${stats.categories} categories`} />
      <Stat label="Units on hand" value={number(stats.totalUnits)} hint="Across all SKUs" />
      <Stat label="Inventory value" value={money(stats.inventoryValue)} hint="Qty × unit price" tone="accent" />
      <Stat label="Low stock" value={number(stats.lowStock)} hint="At or below reorder level" tone="warn" />
      <Stat label="Out of stock" value={number(stats.outOfStock)} hint="Needs reordering now" tone="danger" />
    </section>
  );
}
