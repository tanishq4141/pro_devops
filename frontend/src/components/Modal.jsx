export default function Modal({ eyebrow, title, onClose, children }) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true">
        <div className="modal-head">
          <div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>
          <button type="button" className="close" onClick={onClose} aria-label="Close">×</button>
        </div>
        {children}
      </div>
    </div>
  );
}
