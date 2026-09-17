# Wolf Shoes

Wolf Shoes is a Django-based espadrille store and stock-management platform for men and women in Casablanca, Morocco. It combines a customer storefront, shopping cart, checkout flow, and an admin dashboard for managing products, categories, orders, and in-store POS sales.

This project is designed to be simple, practical, and easy to extend. The core logic lives in the `store` app, and the app uses Django's session-based cart, relational models, and a staff-only admin interface.

## Project overview

The app has three main parts:

- Minimalist monochrome storefront for customers (mobile-optimized)
- Shopping cart and checkout experience with Cash on Delivery (COD)
- Admin dashboard for stock, telemetry, orders, and in-store POS selling

At a high level:

1. Customers browse products on the homepage.
2. They can filter by category, search by keyword, and open a product detail page.
3. Products are added to a cart stored in the user session.
4. At checkout, the user completes an order and the server creates an `Order` plus multiple `OrderItem` records.
5. The stock quantity for each selected size is decreased immediately.
6. Staff users can review orders, update statuses, and process walk-in sales from the admin dashboard.

## Main features

- Minimalist monochrome streetwear aesthetic with clothes-hanger branding
- Product catalog with category filtering and search
- Product detail pages with size and stock information, plus floating mobile Add to Bag CTA
- Thumb-friendly mobile navigation bar with active badges
- Session-based shopping cart with slide-out drawer
- Checkout and order creation with COD (Livraison partout au Maroc 🚚 🇲🇦)
- User registration/login flow during checkout
- Order tracking with statuses such as `PENDING`, `CONFIRMED`, `SHIPPED`, `DELIVERED`, and `CANCELLED`
- Inventory management by item size
- POS sales screen for in-store transactions in Casablanca
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
- `ArticleSize`: size inventory tracking
- `Order`: online or in-store order record
- `OrderItem`: individual line items within an order
- `FeaturedShowcase`: curated lookbook outfits with multiple coordinated articles

The stock system is important: each `Article` can have multiple `ArticleSize` rows. For example:

- Article: "Nike Air Max"
- Sizes: S, M, L, XL
- Stock: 4, 10, 3, 0

A cart item keeps the product ID and selected size. When an order is placed, the app checks stock and decrements the matching `ArticleSize.stock_quantity` value.

### 3. Shopping cart logic

Cart operations live in `store/views/storefront.py` and session helper logic. The session stores a dictionary under the key `'cart'`, where keys are formatted as `"<article_id>_<size>"`.

### 4. Admin and POS workflow

Staff-only views are in `store/views/admin_panel.py`.

The admin panel allows staff to:

- track revenue, total orders, dispatched items, and low-stock alerts
- create, edit, and delete articles, sizes, and categories
- curate lookbook showcases and coordinate outfit pieces
- update order status across the fulfillment lifecycle
- process in-store sales through the dedicated POS terminal

### 5. Multi-language support

Language switching is supported across:

- English (`en`)
- French (`fr`)
- Arabic (`ar`) with complete RTL layout support

Translations and brand metadata are stored in `store/context_processors.py`.

### 6. Django project structure

The main project entry points are:

- `manage.py` - Django command runner
- `clickshop_project/settings.py` - project settings and database config
- `clickshop_project/urls.py` - global routing
- `store/urls.py` - app routes
- `store/models.py` - database models
- `store/views/` - storefront and admin logic
- `store/templates/` - HTML templates
- `static/` - CSS and JS assets
- `media/` - uploaded images

## Project structure

```text
Wolf Shoes/
├── manage.py
├── requirements.txt
├── seed_data.py
├── db.sqlite3
├── README.md
├── media/
├── static/
├── clickshop_project/
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
DB_NAME=wolfshoes_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

The default settings in `clickshop_project/settings.py` are configured for MySQL, but you can also adapt them for SQLite during local development if needed.

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
