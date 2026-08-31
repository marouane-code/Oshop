# Oshop

Oshop is a Django-based online store and stock-management app for a fashion or retail business. It combines a customer storefront, shopping cart, checkout flow, and an admin dashboard for managing products, categories, orders, and in-store POS sales.

This project is designed to be simple, practical, and easy to extend. The core logic lives in the `store` app, and the app uses Django's session-based cart, relational models, and a staff-only admin interface.

## Project overview

The app has three main parts:

- Frontend storefront for customers
- Shopping cart and checkout experience
- Admin dashboard for stock, orders, and POS selling

At a high level:

1. Customers browse products on the homepage.
2. They can filter by category, search by keyword, and open a product detail page.
3. Products are added to a cart stored in the user session.
4. At checkout, the user completes an order and the server creates an `Order` plus multiple `OrderItem` records.
5. The stock quantity for each selected size is decreased immediately.
6. Staff users can review orders, update statuses, and process walk-in sales from the admin dashboard.

## Main features

- Product catalog with category filtering and search
- Product detail pages with size and stock information
- Session-based shopping cart
- Checkout and order creation
- User registration/login flow during checkout
- Order tracking with statuses such as `PENDING`, `CONFIRMED`, `SHIPPED`, `DELIVERED`, and `CANCELLED`
- Inventory management by item size
- POS sales screen for in-store transactions
- Dashboard summary with revenue, order count, and low-stock alerts
- Image upload support for categories and articles

## How the project works

### 1. Storefront flow

The storefront is handled mainly by `store/views/storefront.py` and routed through `store/urls.py`.

Key routes include:

- `/` -> homepage listing products and featured items
- `/article/<slug>/` -> detailed product page
- `/cart/` -> view cart contents
- `/checkout/` -> order form / login / registration flow
- `/place-order/` -> creates the order and updates stock
- `/admin-dashboard/` -> staff admin dashboard
- `/admin-dashboard/pos/` -> in-store sales screen

The homepage loads:

- all active products
- categories
- featured products
- hero banner images

The product list supports filtering by category and keyword search, and the logic is implemented in `home_view()`.

### 2. Product and inventory model

The data model is defined in `store/models.py`.

Important models:

- `Category`: product group
- `Article`: a product entry with price, active status, slug, and images
- `ArticleImage`: product gallery images
- `ArticleSize`: each product can have multiple sizes with stock counts
- `Order`: order header with customer data, total amount, and status
- `OrderItem`: one row per product size in an order
- `UserProfile`: extra customer profile data

The stock system is important: each `Article` can have multiple `ArticleSize` rows. For example:

- Article: "Nike Air Max"
- Sizes: S, M, L, XL
- Stock: 4, 10, 3, 0

A cart item keeps the product ID and selected size. When an order is placed, the app checks stock and decrements the matching `ArticleSize.stock_quantity` value.

### 3. Cart behavior

The cart is stored in the session (`request.session['cart']`). This keeps the shopping cart available without requiring a database entry before checkout.

The session cart is used in:

- `get_cart()`
- `save_cart()`
- `add_to_cart_api()`
- `update_cart_api()`

The cart API endpoints accept JSON and return a success/error response. This is how the frontend updates the cart count and totals without full page reloads.

### 4. Checkout and order creation

The checkout flow is handled in:

- `checkout_view()`
- `place_order_view()`

During checkout:

- the app loads items from the session cart
- validates the user state
- allows login or account creation if needed
- reads name, phone, address, city, and notes
- creates an `Order`
- creates one `OrderItem` per line item
- calculates the total amount
- subtracts stock from each size

This is the moment where the real business logic happens: the order is saved, the stock is reduced, and the order total is finalized.

### 5. Admin dashboard and inventory control

The admin side lives in `store/views/admin_panel.py` and uses staff-only decorators.

It includes:

- `dashboard_view()` for summary metrics
- `sales_chart_data_api()` for chart data
- `pos_sale_view()` for in-store POS sales
- `process_pos_sale_api()` for walk-in transaction processing
- `orders_list_view()` for order management
- `update_order_status_api()` for changing order statuses
- CRUD views for categories and articles

Staff members can:

- view total revenue and sales trends
- see the best-selling products
- track low-stock items
- update order statuses
- sell items directly from POS
- manage categories and articles

### 6. Django project structure

The main project entry points are:

- `manage.py` - Django command runner
- `oshop_project/settings.py` - project settings and database config
- `oshop_project/urls.py` - global routing
- `store/urls.py` - app routes
- `store/models.py` - database models
- `store/views/` - storefront and admin logic
- `store/templates/` - HTML templates
- `static/` - CSS and JS assets
- `media/` - uploaded images

## Project structure

```text
Oshop/
├── manage.py
├── requirements.txt
├── seed_data.py
├── db.sqlite3
├── README.md
├── media/
├── static/
├── oshop_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── models.py
│   ├── urls.py
│   ├── migrations/
│   ├── services/
│   ├── templates/
│   └── views/
│       ├── __init__.py
│       ├── admin_panel.py
│       ├── client_profile.py
│       └── storefront.py
└── staticfiles/
```

## Local setup

### 1. Create and activate a virtual environment

On Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

The project loads values from a `.env` file through `python-dotenv`.

Create a `.env` file in the project root with values like:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=oshop_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

The default settings in `oshop_project/settings.py` are configured for MySQL, but you can also adapt them for SQLite during local development if needed.

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Seed demo data

```bash
python manage.py shell < seed_data.py
```

This script populates sample categories, products, sizes, and related content so the app is usable immediately.

### 7. Run the server

```bash
python manage.py runserver
```

Open the app in the browser:

- Storefront: http://127.0.0.1:8000/
- Django admin: http://127.0.0.1:8000/admin/
- Admin dashboard: http://127.0.0.1:8000/admin-dashboard/
- POS screen: http://127.0.0.1:8000/admin-dashboard/pos/

## Typical workflow

### Customer workflow

1. Visit the homepage.
2. Browse products and filter by category.
3. Open a product detail page.
4. Choose a size and add the item to the cart.
5. Continue to checkout.
6. Log in or register.
7. Submit the order.
8. The system creates the order and updates the stock counts.

### Staff workflow

1. Log in as a staff user.
2. Open the dashboard to review revenue and stock levels.
3. View or update orders.
4. Open the POS screen for walk-in sales.
5. Add product items to a sale, submit the transaction, and reduce stock.

## Notes for contributors

- Keep business logic in the view layer or service layer, not directly inside templates.
- Use Django forms when the app needs more complex validation in the future.
- Be careful with stock updates: the product size check and decrement must happen within the same transaction for consistency.
- Use the app's `Order` and `OrderItem` models as the source of truth for order history and reporting.

## License

This project is intended for internal or business use and can be adapted as needed. You should confirm the licensing terms before distributing or deploying it publicly.
