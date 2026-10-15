export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">S</span>
        <div><b>StockPilot</b><small>Inventory · DevOps Capstone</small></div>
      </div>
      <nav>
        <a className="active">▦ <span>Dashboard</span></a>
        <a>▤ <span>Products</span></a>
        <a>⇅ <span>Stock movements</span></a>
        <a>◎ <span>Suppliers</span></a>
      </nav>
      <div className="side-bottom">
        <div className="upgrade">
          <strong>Never run out.</strong>
          <p>Low-stock alerts are driven by each product's reorder level.</p>
        </div>
        <div className="profile">
          <div className="avatar">TK</div>
          <div><b>Tanishq</b><small>Inventory manager</small></div>
        </div>
      </div>
    </aside>
  );
}
