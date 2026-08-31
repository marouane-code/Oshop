# 👑 O-SHOP — Luxury E-Commerce & Management Platform

<div align="center">

![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Supported-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![CSS3](https://img.shields.io/badge/Vanilla_CSS-Obsidian_&_Gold-D4AF37?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active_Development-10B981?style=for-the-badge)

**A high-performance, trilingual luxury streetwear e-commerce platform with a built-in Point of Sale (POS) and administrative management suite.**

[Quick Run Guide](#-how-to-run-the-project-step-by-step) • [Features](#-key-features) • [Architecture](#-project-structure) • [Localization](#-multi-language--rtl-support) • [Git Collaboration](#-collaborating-with-git)

---

</div>

## 🚀 How to Run the Project (Step-by-Step)

Follow these exact steps to clone, configure, and launch the application on your computer:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/oshop.git
cd oshop
```

---

### 2️⃣ Set Up Virtual Environment

<details open>
<summary><b>🪟 On Windows (PowerShell or Command Prompt)</b></summary>

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate
```
*(If PowerShell gives an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and retry activating).*
</details>

<details>
<summary><b>🍎 On macOS / 🐧 Linux</b></summary>

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```
</details>

---

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4️⃣ Environment Configuration (`.env`)
Create your local environment file by copying the template:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

> **Note**: If you are using **SQLite** (default for local development), no changes are required in `.env`.
> If using **MySQL**, update the credentials inside `.env`:
```env
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
DB_NAME=oshop_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

### 5️⃣ Initialize Database & Seed Demo Data
Run migrations to set up database tables, then populate the catalog with demo items:

```bash
# 1. Apply database migrations
python manage.py migrate

# 2. Seed initial categories, luxury articles, sizes, and demo images
python manage.py shell < seed_data.py

# 3. Create your Administrator account
python manage.py createsuperuser
```
*(Follow the prompt to enter username, email, and password for admin access).*

---

### 6️⃣ Run Development Server
```bash
python manage.py runserver
```

Once running, access the portals in your browser:

| Portal | URL | Description |
| :--- | :--- | :--- |
| **🛍️ Client Storefront** | [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/) | Customer catalog, hero slideshow & checkout |
| **📊 Admin Dashboard** | [`http://127.0.0.1:8000/admin-panel/dashboard/`](http://127.0.0.1:8000/admin-panel/dashboard/) | SaaS analytics, metrics & stock levels |
| **💳 POS Terminal** | [`http://127.0.0.1:8000/admin-panel/pos/`](http://127.0.0.1:8000/admin-panel/pos/) | In-store point-of-sale checkout |
| **📦 Order Management** | [`http://127.0.0.1:8000/admin-panel/orders/`](http://127.0.0.1:8000/admin-panel/orders/) | Status tracking (Pending → Shipped → Delivered) |
| **⚙️ Django Admin** | [`http://127.0.0.1:8000/admin/`](http://127.0.0.1:8000/admin/) | Backend database administration |

---

## ✨ Key Features

### 🛍️ Client Storefront
- **Luxury Dark Mode Aesthetic**: High-contrast obsidian backgrounds, gold gradient accents, glassmorphic header (`backdrop-filter`), and fluid micro-animations.
- **Dynamic Hero Banner**: Auto-shuffling interactive photo gallery showcasing active collection articles on every page load with smooth fade transitions.
- **Responsive Mobile Navigation**: Clean sticky navigation with auto-collapsing search drawer, slide-down mobile menu, and slide-over Shopping Bag cart drawer (`100dvh` viewport safe).
- **Product Catalog & Filtering**: Real-time category filtering, search queries, multi-size stock indicators, and instant order placement.
- **Direct WhatsApp & COD Checkout**: Streamlined Cash-on-Delivery (COD) checkout tailored for the Moroccan market with automated WhatsApp order links.

### 🛡️ Admin & POS Portal
- **Dedicated SaaS Admin Layout**: Fixed sidebar navigation with real-time sales metrics and low-stock alerts.
- **Point of Sale (POS) Terminal**: Quick in-person walk-in order entry with dynamic item search, live total calculations, and receipt generation.
- **Order & Inventory Management**: Track and update status orders (`Pending`, `Confirmed`, `Shipped`, `Delivered`, `Cancelled`) with stock level adjustments.
- **Multi-Language Admin Controls**: Admin panel toggle for English, French, and Arabic.

---

## 🌐 Multi-Language & RTL Support

O-Shop includes built-in localization across both client storefront and admin console:

| Language | Code | Direction | Support |
| :--- | :--- | :--- | :--- |
| **English** | `en` | LTR (`dir="ltr"`) | Full Storefront & Admin |
| **Français** | `fr` | LTR (`dir="ltr"`) | Full Storefront & Admin |
| **العربية (Arabic)** | `ar` | RTL (`dir="rtl"`) | Full Storefront, Admin & Mirrored Layouts |

Language choice is automatically persisted across user sessions via session state.

---

## 📂 Project Structure

```
Oshop/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── seed_data.py                # Database population script
├── .env.example                # Example environment configuration
├── .gitignore                  # Git exclusions
│
├── oshop_project/              # Core Django Settings & Configuration
│   ├── settings.py             # App configs, database routing & middleware
│   ├── urls.py                 # Root URL router & media serving
│   └── wsgi.py                 # WSGI entry point
│
├── store/                      # Main Application Module
│   ├── models.py               # Category, Article, ArticleSize, Order, OrderItem
│   ├── views/
│   │   ├── storefront.py       # Catalog, product details, cart & checkout views
│   │   └── admin_views.py      # POS, inventory management & analytics views
│   ├── context_processors.py   # Multi-language dictionaries & cart counter
│   ├── templates/
│   │   ├── base.html           # Master storefront layout & navigation
│   │   ├── store/              # Customer-facing views (home, detail, checkout)
│   │   └── admin_panel/        # Admin portal views (dashboard, POS, orders)
│   └── urls.py                 # Storefront & admin routing definitions
│
├── static/                     # Static Assets
│   ├── css/
│   │   ├── main.css            # Storefront design system & responsive rules
│   │   └── admin.css           # Admin sidebar, table styles & RTL overrides
│   └── js/
│       └── cart.js             # Cart drawer interactions & quantity updates
│
└── media/                      # Uploaded product imagery
```

---

## 🤝 Collaborating with Git

### How to push your updates:
```bash
git add .
git commit -m "feat: description of your changes"
git push origin main
```

### For your collaborator:
1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/awesome-feature
   ```
3. **Commit & Push branch**:
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   git push origin feature/awesome-feature
   ```
4. **Open a Pull Request (PR)** on GitHub to merge into `main`.

---

## 📄 License
This project is proprietary and built exclusively for **O-SHOP Safi, Morocco**. All rights reserved.
