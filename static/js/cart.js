document.addEventListener('DOMContentLoaded', () => {
  const cartDrawer = document.getElementById('cartDrawer');
  const cartOverlay = document.getElementById('cartOverlay');
  const cartTriggers = document.querySelectorAll('.trigger-cart');
  const cartClose = document.getElementById('cartClose');

  function openCart() {
    if (cartDrawer && cartOverlay) {
      cartDrawer.classList.add('active');
      cartOverlay.classList.add('active');
    }
  }

  function closeCart() {
    if (cartDrawer && cartOverlay) {
      cartDrawer.classList.remove('active');
      cartOverlay.classList.remove('active');
    }
  }

  cartTriggers.forEach(btn => btn.addEventListener('click', openCart));
  if (cartClose) cartClose.addEventListener('click', closeCart);
  if (cartOverlay) cartOverlay.addEventListener('click', closeCart);

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
  window.addToCart = async function(articleId, size, quantity = 1) {
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
          quantity: quantity
        })
      });

      const data = await response.json();
      if (data.success) {
        // Update cart count badges
        const badges = document.querySelectorAll('.cart-badge-count');
        badges.forEach(b => b.textContent = data.cart_count);
        openCart();
        // Refresh page or cart contents if needed
        location.reload();
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
        location.reload();
      } else {
        alert(data.message || "Failed to update item.");
      }
    } catch (err) {
      console.error(err);
    }
  };
});
