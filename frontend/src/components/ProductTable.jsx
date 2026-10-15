import { money, number, STATUS_LABEL } from '../format.js';

const FILTERS = ['ALL', 'IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK'];

export default function ProductTable({ products, loading, filter, onFilter, search, onSearch, onAdjust, onEdit, onDelete }) {
  return (
    <div className="panel products-panel">
      <div className="panel-head">
        <div>
          <h2>Products</h2>
          <p className="muted">Live stock levels from PostgreSQL.</p>
        </div>
        <input className="search" placeholder="Search name, SKU, supplier…" value={search} onChange={(e) => onSearch(e.target.value)} />
      </div>
      <div className="filters">
        {FILTERS.map((f) => (
          <button key={f} className={filter === f ? 'selected' : ''} onClick={() => onFilter(f)}>
            {f === 'ALL' ? 'All' : STATUS_LABEL[f]}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="empty">Loading products…</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Product</th><th>Category</th><th className="num">Qty</th><th className="num">Unit price</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="product-cell">
                      <span className={`dot ${p.stock_status.toLowerCase()}`} />
                      <div><b>{p.name}</b><small>{p.sku} · {p.supplier}</small></div>
                    </div>
                  </td>
                  <td>{p.category}</td>
                  <td className="num"><b>{number(p.quantity)}</b><small>reorder at {p.reorder_level}</small></td>
                  <td className="num">{money(p.unit_price)}</td>
                  <td><span className={`badge ${p.stock_status.toLowerCase()}`}>{STATUS_LABEL[p.stock_status]}</span></td>
                  <td className="actions">
                    <button className="icon-btn" title="Adjust stock" onClick={() => onAdjust(p)}>⇅</button>
                    <button className="icon-btn" title="Edit" onClick={() => onEdit(p)}>✎</button>
                    <button className="icon-btn danger" title="Delete" onClick={() => onDelete(p)}>🗑</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!products.length && <div className="empty">No products match this view.</div>}
        </div>
      )}
    </div>
  );
}
