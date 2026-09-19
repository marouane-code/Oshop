document.addEventListener('DOMContentLoaded', () => {
  const articlesJsonElem = document.getElementById('articlesDataJson');
  if (!articlesJsonElem) return;

  const articlesData = JSON.parse(articlesJsonElem.textContent);
  let posCart = [];

  const articleSelect = document.getElementById('posArticleSelect');
  const colorGroup = document.getElementById('posColorGroup');
  const colorSelect = document.getElementById('posColorSelect');
  const sizeSelect = document.getElementById('posSizeSelect');
  const qtyInput = document.getElementById('posQtyInput');
  const addBtn = document.getElementById('posAddBtn');
  const cartTableBody = document.getElementById('posCartBody');
  const totalAmountElem = document.getElementById('posTotalAmount');
  const checkoutBtn = document.getElementById('posCheckoutBtn');

  function updateArticleSelection() {
    const selectedArticleId = parseInt(articleSelect.value);
    const article = articlesData.find(a => a.id === selectedArticleId);
    
    if (!article) return;

    if (article.has_colors && article.colors && article.colors.length > 0) {
      if (colorGroup) colorGroup.style.display = 'block';
      colorSelect.innerHTML = '';
      article.colors.forEach(col => {
        const opt = document.createElement('option');
        opt.value = col;
        opt.textContent = col;
        colorSelect.appendChild(opt);
      });
    } else {
      if (colorGroup) colorGroup.style.display = 'none';
      colorSelect.innerHTML = '';
    }

    updateSizes();
  }

  // Populate Sizes dropdown on article / color change
  function updateSizes() {
    const selectedArticleId = parseInt(articleSelect.value);
    const article = articlesData.find(a => a.id === selectedArticleId);
    sizeSelect.innerHTML = '';

    if (!article || !article.sizes) return;

    const selectedColor = (colorGroup && colorGroup.style.display !== 'none') ? colorSelect.value : '';

    const matchingVariants = article.sizes.filter(s => {
      if (selectedColor) {
        return s.color === selectedColor;
      }
      return true;
    });

    matchingVariants.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.size;
      const colLabel = s.color ? `[${s.color}] ` : '';
      opt.textContent = `${colLabel}${s.size} (${s.stock} in stock)`;
      if (s.stock <= 0) opt.disabled = true;
      sizeSelect.appendChild(opt);
    });
  }

  if (articleSelect) {
    articleSelect.addEventListener('change', updateArticleSelection);
    if (colorSelect) {
      colorSelect.addEventListener('change', updateSizes);
    }
    updateArticleSelection();
  }

  function renderPosCart() {
    cartTableBody.innerHTML = '';
    let grandTotal = 0;

    posCart.forEach((item, index) => {
      const subtotal = item.price * item.quantity;
      grandTotal += subtotal;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div style="display:flex; align-items:center; gap:0.75rem;">
            ${item.image ? `<img src="${item.image}" style="width:40px; height:45px; object-fit:cover; border-radius:4px;">` : ''}
            <div>
              <strong>${item.title}</strong>
              <div style="font-size:0.8rem; color:var(--text-muted);">${item.category}</div>
            </div>
          </div>
        </td>
        <td>
          <span class="size-pill selected">${item.size}</span>
          ${item.color ? `<span style="font-size:0.75rem; background:var(--admin-bg-elevated); padding:2px 6px; border-radius:4px; border:1px solid var(--admin-border-gold); color:var(--gold-bright); margin-left:4px; font-weight:700;">${item.color}</span>` : ''}
        </td>
        <td>${item.price.toFixed(2)} MAD</td>
        <td>
          <input type="number" min="1" value="${item.quantity}" style="width:60px;" class="form-control" onchange="window.updatePosQty(${index}, this.value)">
        </td>
        <td style="font-weight:700; color:var(--gold-bright);">${subtotal.toFixed(2)} MAD</td>
        <td>
          <button class="btn btn-dark" style="padding:0.3rem 0.6rem;" onclick="window.removePosItem(${index})">✕</button>
        </td>
      `;
      cartTableBody.appendChild(tr);
    });

    totalAmountElem.textContent = `${grandTotal.toFixed(2)} MAD`;
    if (checkoutBtn) checkoutBtn.disabled = posCart.length === 0;
  }

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      const artId = parseInt(articleSelect.value);
      const article = articlesData.find(a => a.id === artId);
      const size = sizeSelect.value;
      const color = (colorGroup && colorGroup.style.display !== 'none') ? colorSelect.value : '';
      const qty = parseInt(qtyInput.value) || 1;

      if (!article || !size) {
        alert("Select article and size");
        return;
      }

      const sizeObj = article.sizes.find(s => s.size === size && (color ? s.color === color : true));
      if (!sizeObj || sizeObj.stock < qty) {
        const desc = size + (color ? ` (${color})` : '');
        alert(`Only ${sizeObj ? sizeObj.stock : 0} items available for ${desc}.`);
        return;
      }

      const existing = posCart.find(i => i.article_id === artId && i.size === size && (i.color || '') === (color || ''));
      if (existing) {
        if (existing.quantity + qty > sizeObj.stock) {
          alert(`Cannot add more than total stock (${sizeObj.stock})`);
          return;
        }
        existing.quantity += qty;
      } else {
        posCart.push({
          article_id: article.id,
          title: article.title,
          category: article.category,
          price: article.price,
          size: size,
          color: color,
          quantity: qty,
          image: article.image
        });
      }

      renderPosCart();
    });
  }

  window.updatePosQty = function(index, newQty) {
    const qty = parseInt(newQty);
    if (qty > 0) {
      posCart[index].quantity = qty;
      renderPosCart();
    }
  };

  window.removePosItem = function(index) {
    posCart.splice(index, 1);
    renderPosCart();
  };

  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', async () => {
      if (posCart.length === 0) return;

      const notes = document.getElementById('posNotesInput')?.value || 'In-Store Walk-In Sale';

      try {
        const response = await fetch('/admin-dashboard/pos/process/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
          },
          body: JSON.stringify({ items: posCart, notes: notes })
        });

        const data = await response.json();
        if (data.success) {
          alert(`✅ ${data.message}`);
          posCart = [];
          renderPosCart();
          location.reload();
        } else {
          alert(`❌ Error: ${data.message}`);
        }
      } catch (err) {
        console.error(err);
        alert("Server error processing sale.");
      }
    });
  }
});
