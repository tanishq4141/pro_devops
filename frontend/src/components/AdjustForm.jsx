import { useState } from 'react';
import Modal from './Modal.jsx';

const REASONS = ['RESTOCK', 'SALE', 'RETURN', 'DAMAGED', 'CORRECTION'];

export default function AdjustForm({ product, onSave, onClose }) {
  const [error, setError] = useState('');
  const [direction, setDirection] = useState('in');

  const submit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const amount = Math.abs(Number(f.get('amount')));
    try {
      await onSave({ change: direction === 'in' ? amount : -amount, reason: f.get('reason'), note: f.get('note') });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Modal eyebrow="ADJUST STOCK" title={`${product.name} · ${product.quantity} on hand`} onClose={onClose}>
      <form onSubmit={submit}>
        {error && <div className="alert">{error}</div>}
        <div className="segmented">
          <button type="button" className={direction === 'in' ? 'selected' : ''} onClick={() => setDirection('in')}>Stock in</button>
          <button type="button" className={direction === 'out' ? 'selected' : ''} onClick={() => setDirection('out')}>Stock out</button>
        </div>
        <div className="form-row">
          <label>Quantity<input name="amount" type="number" min="1" required defaultValue="1" /></label>
          <label>Reason
            <select name="reason" defaultValue={direction === 'in' ? 'RESTOCK' : 'SALE'} key={direction}>
              {REASONS.map((r) => <option key={r}>{r}</option>)}
            </select>
          </label>
        </div>
        <label>Note<input name="note" placeholder="PO number, order id…" /></label>
        <button className="primary full">Record movement</button>
      </form>
    </Modal>
  );
}
