document.addEventListener('DOMContentLoaded', () => {
  const cartDrawer = document.getElementById('cartDrawer');
  const cartTriggers = document.querySelectorAll('.trigger-cart');
  const cartClose = document.getElementById('closeCartDrawerBtn');
  const cartItems = document.getElementById('cartDrawerItems');
  const cartSubtotal = document.getElementById('cartDrawerSubtotal');

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function formatMoney(value) {
    return `${Number(value || 0).toFixed(2)} MAD`;
  }

  function renderCart(data) {
    document.querySelectorAll('.cart-badge-count').forEach(badge => {
      badge.textContent = data.cart_count || 0;
    });

    if (cartSubtotal) cartSubtotal.textContent = formatMoney(data.subtotal);
    if (!cartItems) return;

    if (!data.items || data.items.length === 0) {
      cartItems.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:2rem 0;">Votre panier est vide.</p>';
      return;
    }

    cartItems.innerHTML = data.items.map(item => `
      <div style="display:flex; gap:0.75rem; padding-bottom:1rem; margin-bottom:1rem; border-bottom:1px solid var(--border-color);">
        <div style="width:58px; height:70px; flex-shrink:0; border-radius:6px; overflow:hidden; background:#F3F4F6;">
          ${item.image ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" style="width:100%; height:100%; object-fit:cover;">` : '<div style="height:100%; display:flex; align-items:center; justify-content:center; font-size:0.65rem; color:var(--text-muted);">Mario</div>'}
        </div>
        <div style="flex:1; min-width:0;">
          <strong style="display:block; font-size:0.85rem; line-height:1.3;">${escapeHtml(item.title)}</strong>
          <div style="font-size:0.74rem; color:var(--text-muted); margin-top:0.25rem;">Taille: ${escapeHtml(item.size)}${item.color ? ` | Couleur: ${escapeHtml(item.color)}` : ''}</div>
          <div style="display:flex; align-items:center; justify-content:space-between; gap:0.5rem; margin-top:0.5rem;">
            <span style="font-size:0.78rem;">${item.quantity} x ${formatMoney(item.unit_price)}</span>
            <strong style="font-size:0.85rem;">${formatMoney(item.subtotal)}</strong>
          </div>
          <div style="display:flex; gap:0.35rem; margin-top:0.45rem;">
            <button type="button" data-cart-action="decrease" data-cart-key="${escapeHtml(item.key)}" style="border:1px solid var(--border-color); background:#fff; cursor:pointer; padding:0.1rem 0.4rem;">-</button>
            <button type="button" data-cart-action="increase" data-cart-key="${escapeHtml(item.key)}" style="border:1px solid var(--border-color); background:#fff; cursor:pointer; padding:0.1rem 0.4rem;">+</button>
            <button type="button" data-cart-action="remove" data-cart-key="${escapeHtml(item.key)}" style="border:0; background:none; color:#C5221F; cursor:pointer; font-size:0.72rem; margin-left:auto;">Supprimer</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  async function loadCart() {
    try {
      const response = await fetch('/api/cart/contents/', { headers: { 'Accept': 'application/json' } });
      if (!response.ok) throw new Error('Unable to load cart contents');
      const data = await response.json();
      renderCart(data);
      return data;
    } catch (error) {
      console.error(error);
      if (cartItems) cartItems.innerHTML = '<p style="text-align:center; color:#C5221F; padding:2rem 0;">Impossible de charger le panier.</p>';
      return null;
    }
  }

  function openCart() {
    if (!cartDrawer) return;
    cartDrawer.style.display = 'block';
    document.body.style.overflow = 'hidden';
    loadCart();
  }

  function closeCart() {
    if (!cartDrawer) return;
    cartDrawer.style.display = 'none';
    document.body.style.overflow = '';
  }

  window.openCartDrawer = openCart;

  cartTriggers.forEach(btn => btn.addEventListener('click', openCart));
  if (cartClose) cartClose.addEventListener('click', closeCart);
  if (cartDrawer) cartDrawer.addEventListener('click', event => {
    if (event.target === cartDrawer) closeCart();
  });
  if (cartItems) cartItems.addEventListener('click', event => {
    const button = event.target.closest('[data-cart-action]');
    if (button) updateCartItem(button.dataset.cartKey, button.dataset.cartAction);
  });

  // CSRF token helper
  function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Global Add to Cart function
  window.addToCart = async function(articleId, size, color = '', quantity = 1) {
    if (articleId && typeof articleId === 'object') {
      ({ articleId, size, color = '', quantity = 1 } = articleId);
    }

    if (typeof color === 'number') {
      quantity = color;
      color = '';
    }

    quantity = Number.parseInt(quantity, 10);
    if (!Number.isInteger(quantity) || quantity < 1) {
      quantity = 1;
    }

    if (!size) {
      alert("Please select a size first!");
      return;
    }

    try {
      const response = await fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          article_id: articleId,
          size: size,
          color: color || '',
          quantity: quantity
        })
      });

      const data = await response.json();
      if (data.success) {
        await loadCart();
        openCart();
      } else {
        alert(data.message || "Could not add item to cart.");
      }
    } catch (err) {
      console.error(err);
      alert("Network error occurred.");
    }
  };

  // Cart update API call
  window.updateCartItem = async function(key, action) {
    try {
      const response = await fetch('/api/cart/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ key, action })
      });
      const data = await response.json();
      if (data.success) {
        await loadCart();
        openCart();
      } else {
        alert(data.message || "Failed to update item.");
      }
    } catch (err) {
      console.error(err);
    }
  };
});
