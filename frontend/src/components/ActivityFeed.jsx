import { timeAgo } from '../format.js';

const ICON = { RESTOCK: '＋', SALE: '−', RETURN: '↩', DAMAGED: '!', CORRECTION: '≈' };

export default function ActivityFeed({ movements }) {
  return (
    <aside className="panel activity">
      <div className="panel-head">
        <div><h2>Stock movements</h2><p className="muted">Every change is audited.</p></div>
      </div>
      {movements.length === 0 && <div className="empty small">No movements yet — adjust a product's stock.</div>}
      {movements.map((m) => (
        <div className="activity-row" key={m.id}>
          <span className={`activity-icon ${m.change > 0 ? 'in' : 'out'}`}>{ICON[m.reason]}</span>
          <div>
            <b>{m.change > 0 ? '+' : ''}{m.change} · {m.product_name}</b>
            <small>{m.reason.toLowerCase()}{m.note ? ` · ${m.note}` : ''} · {timeAgo(m.created_at)}</small>
          </div>
        </div>
      ))}
      <div className="pipeline" title="Delivery pipeline">
        <span>Test</span><i /><span>Build</span><i /><span>Scan</span><i /><span>Deploy</span>
      </div>
    </aside>
  );
}
