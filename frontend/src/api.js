const API = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : body.detail[0]?.msg ?? detail;
    } catch { /* non-JSON error body */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  listProducts: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/products${query ? `?${query}` : ''}`);
  },
  stats: () => request('/products/stats'),
  movements: (limit = 8) => request(`/movements?limit=${limit}`),
  createProduct: (data) => request('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),
  adjustStock: (id, data) => request(`/products/${id}/adjust`, { method: 'POST', body: JSON.stringify(data) }),
};
