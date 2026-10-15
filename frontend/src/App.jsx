import { useCallback, useEffect, useState } from 'react';
import { api } from './api.js';
import Sidebar from './components/Sidebar.jsx';
import StatCards from './components/StatCards.jsx';
import ProductTable from './components/ProductTable.jsx';
import ActivityFeed from './components/ActivityFeed.jsx';
import ProductForm from './components/ProductForm.jsx';
import AdjustForm from './components/AdjustForm.jsx';

const EMPTY_STATS = { totalProducts: 0, totalUnits: 0, inventoryValue: 0, lowStock: 0, outOfStock: 0, categories: 0 };

export default function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [movements, setMovements] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null); // {type: 'create'|'edit'|'adjust', product}

  const load = useCallback(async () => {
    try {
      setError('');
      const [p, s, m] = await Promise.all([
        api.listProducts({ q: search, status: filter === 'ALL' ? '' : filter }),
        api.stats(),
        api.movements(8),
      ]);
      setProducts(p);
      setStats(s);
      setMovements(m);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, filter]);

  useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
  }, [load]);

  const close = () => setModal(null);
  const afterSave = async () => { close(); await load(); };

  const remove = async (p) => {
    if (!window.confirm(`Delete ${p.name} (${p.sku})?`)) return;
    try { await api.deleteProduct(p.id); await load(); } catch (e) { setError(e.message); }
  };

  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        <header>
          <div>
            <p className="eyebrow">WAREHOUSE / OVERVIEW</p>
            <h1>Inventory dashboard</h1>
            <p className="muted">Stock levels, value and movements across your catalogue.</p>
          </div>
          <button className="primary" onClick={() => setModal({ type: 'create' })}>＋ Add product</button>
        </header>
        {error && <div className="alert">⚠ {error}. Check that the backend and PostgreSQL are running.</div>}
        <StatCards stats={stats} />
        <section className="content-grid">
          <ProductTable
            products={products} loading={loading}
            filter={filter} onFilter={setFilter}
            search={search} onSearch={setSearch}
            onAdjust={(p) => setModal({ type: 'adjust', product: p })}
            onEdit={(p) => setModal({ type: 'edit', product: p })}
            onDelete={remove}
          />
          <ActivityFeed movements={movements} />
        </section>
      </main>
      {modal?.type === 'create' && <ProductForm onClose={close} onSave={async (d) => { await api.createProduct(d); await afterSave(); }} />}
      {modal?.type === 'edit' && <ProductForm product={modal.product} onClose={close} onSave={async (d) => { await api.updateProduct(modal.product.id, d); await afterSave(); }} />}
      {modal?.type === 'adjust' && <AdjustForm product={modal.product} onClose={close} onSave={async (d) => { await api.adjustStock(modal.product.id, d); await afterSave(); }} />}
    </div>
  );
}
