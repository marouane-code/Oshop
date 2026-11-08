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
      cartItems.innerHTML = `
        <div style="text-align:center; color:var(--text-muted); padding:3rem 1rem;">
          <div style="display:flex; justify-content:center; margin-bottom:0.75rem; color:#9CA3AF;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
          </div>
          <p style="font-weight:800; color:#0A0A0A; font-size:1rem; margin-bottom:0.35rem;">Votre panier est vide</p>
          <p style="font-size:0.82rem; color:var(--text-muted);">Explorez notre collection pour ajouter des articles.</p>
        </div>
      `;
      return;
    }

    cartItems.innerHTML = data.items.map(item => `
      <div class="cart-drawer-item">
        <div class="cart-drawer-item-img">
          ${item.image ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}">` : '<div class="cart-drawer-item-placeholder">Mario</div>'}
        </div>
        <div class="cart-drawer-item-details">
          <strong class="cart-drawer-item-title">${escapeHtml(item.title)}</strong>
          <div class="cart-drawer-item-meta">Taille: <span>${escapeHtml(item.size)}</span>${item.color ? ` | Couleur: <span>${escapeHtml(item.color)}</span>` : ''}</div>
          <div class="cart-drawer-item-price-row">
            <span class="cart-drawer-item-unit">${item.quantity} × ${formatMoney(item.unit_price)}</span>
            <strong class="cart-drawer-item-subtotal">${formatMoney(item.subtotal)}</strong>
          </div>
          <div class="cart-drawer-item-actions">
            <div class="cart-qty-pill">
              <button type="button" class="cart-qty-btn" data-cart-action="decrease" data-cart-key="${escapeHtml(item.key)}" aria-label="Diminuer">−</button>
              <span class="cart-qty-num">${item.quantity}</span>
              <button type="button" class="cart-qty-btn" data-cart-action="increase" data-cart-key="${escapeHtml(item.key)}" aria-label="Augmenter">+</button>
            </div>
            <button type="button" class="cart-item-remove-btn" data-cart-action="remove" data-cart-key="${escapeHtml(item.key)}">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
              Supprimer
            </button>
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
  window.closeCartDrawer = closeCart;
  window.loadCartDrawer = loadCart;

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
