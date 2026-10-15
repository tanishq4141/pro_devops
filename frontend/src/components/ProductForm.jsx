import { useState } from 'react';
import Modal from './Modal.jsx';

export default function ProductForm({ product, onSave, onClose }) {
  const editing = Boolean(product);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const data = {
      name: f.get('name'),
      description: f.get('description'),
      category: f.get('category') || 'General',
      supplier: f.get('supplier') || 'Unknown',
      reorder_level: Number(f.get('reorder_level')),
      unit_price: f.get('unit_price') || '0',
    };
    if (!editing) {
      data.sku = f.get('sku');
      data.quantity = Number(f.get('quantity'));
    }
    try {
      await onSave(data);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Modal eyebrow={editing ? 'EDIT PRODUCT' : 'NEW PRODUCT'} title={editing ? product.name : 'Add a product'} onClose={onClose}>
      <form onSubmit={submit}>
        {error && <div className="alert">{error}</div>}
        <div className="form-row">
          <label>SKU<input name="sku" required={!editing} disabled={editing} defaultValue={product?.sku} placeholder="ELEC-1003" pattern="[A-Za-z0-9-]+" /></label>
          <label>Category<input name="category" defaultValue={product?.category ?? 'General'} /></label>
        </div>
        <label>Product name<input name="name" required defaultValue={product?.name} placeholder="e.g. Bluetooth Keyboard" /></label>
        <label>Description<textarea name="description" defaultValue={product?.description} /></label>
        <label>Supplier<input name="supplier" defaultValue={product?.supplier ?? ''} placeholder="Supplier name" /></label>
        <div className="form-row three">
          <label>Opening qty<input name="quantity" type="number" min="0" defaultValue={product?.quantity ?? 0} disabled={editing} /></label>
          <label>Reorder level<input name="reorder_level" type="number" min="0" defaultValue={product?.reorder_level ?? 10} /></label>
          <label>Unit price (₹)<input name="unit_price" type="number" min="0" step="0.01" defaultValue={product?.unit_price ?? ''} /></label>
        </div>
        <button className="primary full">{editing ? 'Save changes' : 'Create product'}</button>
      </form>
    </Modal>
  );
}
