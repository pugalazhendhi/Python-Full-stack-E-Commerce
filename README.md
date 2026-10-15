# ShopSphere — Modern Online Shopping Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**ShopSphere** is a modern, enterprise-ready Python full-stack e-commerce web platform engineered with clean architectural principles, server-side data validation, atomic database transactions, dynamic AJAX user interactions, and an intuitive UI/UX design.

---

## 🌟 Key Highlights & Features

### 1. Storefront & Home Experience
- **Interactive Hero Showcase:** High-impact promotion banners with instant call-to-action buttons.
- **Dynamic Category Navigation:** Automatically generated category pills and dropdowns powered by custom context processors.
- **Curated Merchandising Strips:** Featured items, Best Sellers, and New Arrivals.
- **Customer Feedback & Testimonials:** Real verified review cards showcasing rating stars and feedback.
- **Global Live Search:** Auto-suggest dropdown with debounced AJAX endpoint querying products in real-time.

### 2. Product Catalog, Filtering & Search
- **Responsive Product Grid:** High-res image cards, discount tags, price strikes, and stock indicators.
- **Multi-Faceted Filtering:** 
  - Instant category filtering
  - Price range min/max filtering
  - In-stock availability toggle
- **Dynamic Sorting:** Sort by *Newest*, *Price: Low to High*, *Price: High to Low*, *Popularity*, and *Customer Rating*.
- **Pagination:** Clean, accessible page controls (12 items/page).
- **Graceful Empty State:** Friendly feedback when no products match search criteria.

### 3. Product Details & Reviews
- **Multi-Image Gallery:** Interactive thumbnail gallery switcher.
- **Detailed Specifications Table:** Structured tabular layout for technical parameters.
- **Real-Time Stock Badge:** Immediate visual indicator of units available or out-of-stock badge.
- **Star Rating & Verified Reviews:** Customers can submit 1–5 star ratings, headline, and comment with automated average rating recalculation.
- **Related Products Carousel:** Contextual recommendations based on category.

### 4. Shopping Cart & Inventory Security
- **Strict Server-Side Validation:** All prices, stock counts, discounts, and totals are computed strictly on the server; browser manipulations are impossible.
- **AJAX Add & Quantity Update:** Instant toast notifications without page reloads.
- **Stock Limit Enforcement:** Capped at available warehouse stock; users cannot order unavailable units.
- **Free Shipping Progress Bar:** Real-time visual progress showing how much more to add to unlock free shipping ($500 threshold).
- **Session Cart Synchronization:** Guest carts automatically merge into the user account upon login.

### 5. Checkout & Order Management
- **Address Management:** Select from saved shipping addresses or enter a new address on the fly.
- **Coupon & Promo Code Engine:** Validates percentage or flat discounts with minimum subtotal requirements.
- **Atomic Database Transactions:** Uses `transaction.atomic()` and `select_for_update()` to ensure orders and inventory deductions succeed or roll back together.
- **Cash on Delivery (COD) & Gateway-Ready:** Working COD checkout with modular structure ready for Razorpay or Stripe integration.
- **Order Tracking Stepper:** Visual tracking pipeline: *Pending → Confirmed → Shipped → Delivered*.
- **Self-Service Order Cancellation:** Customers can cancel orders while in *Pending* or *Confirmed* status; product inventory is automatically restored upon cancellation.
- **Historical Accuracy:** Snapshots product titles, SKUs, and unit prices at the time of purchase.

### 6. Wishlist
- **AJAX Wishlist Toggle:** Instant heart icon state toggle.
- **Duplicate Prevention:** Unique constraint per user and product.
- **Move to Cart:** One-click transfer from wishlist directly into the active shopping cart.

### 7. User Authentication & Profiles
- Built upon a custom `User` model inheriting from Django's `AbstractUser`.
- User registration with unique email enforcement and password validation.
- Profile management, password change with session preservation, and multiple shipping addresses CRUD.
- Order history with full printable invoice receipts.

### 8. Custom Django Admin Dashboard
- Clean store administration portal (`/admin/`).
- Product inline gallery management and thumbnail previews.
- Quick bulk actions: Approve reviews, advance order statuses, or cancel and restore inventory.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3, Bootstrap Icons |
| **Backend** | Python 3.11+, Django 5.2, Django REST Framework |
| **Database** | MySQL 8.0 / SQLite (configurable via environment variables) |
| **Libraries** | PyMySQL, Pillow (Image Processing), python-dotenv, Cryptography |
| **Architecture** | Model-View-Template (MVT) + REST API endpoints |

---

## 📂 Project Architecture

```
d:/e-commerce/
├── apps/
│   ├── accounts/          # User auth, profile, and address management
│   ├── catalog/           # Categories, products, reviews, and search
│   ├── cart/              # Database-backed cart, sessions, and calculations
│   ├── orders/            # Orders, coupons, checkout, and inventory rollback
│   └── wishlist/          # Customer saved wishlist
├── config/
│   ├── settings.py        # Environment-driven Django configuration
│   ├── urls.py            # Global URL routing
│   ├── wsgi.py            # WSGI production entrypoint
│   └── asgi.py            # ASGI asynchronous entrypoint
├── templates/
│   ├── base.html          # Global header, navbar, footer & toast container
│   ├── accounts/          # Login, register, profile, addresses
│   ├── catalog/           # Home, product list, product detail
│   ├── cart/              # Cart detail & summary
│   ├── orders/            # Checkout, confirmation, history, invoices
│   └── wishlist/          # Saved products
├── static/
│   ├── css/style.css      # Custom design system & animations
│   ├── js/main.js         # AJAX cart, wishlist, and auto-suggest
│   └── images/            # Static placeholders & brand assets
├── media/                 # Uploaded product and category imagery
├── requirements.txt       # Project dependencies
├── .env.example           # Environment template
├── .gitignore             # Git exclusions
├── manage.py              # CLI management script
└── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup Guide

### 1. Prerequisites
- Python 3.11 or higher installed
- MySQL Server 8.0 running locally or remotely (optional; fallback to SQLite supported)
- Git version control

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/your-username/shopsphere.git
cd shopsphere

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Variable Configuration
Copy the provided `.env.example` into a new `.env` file:
```bash
copy .env.example .env
```

Configure your MySQL credentials in `.env`:
```env
DEBUG=True
SECRET_KEY=your-secure-random-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# MySQL Database Configuration
DB_ENGINE=mysql
DB_NAME=shopsphere
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Set USE_SQLITE=False once MySQL credentials are provided
USE_SQLITE=False
```

> **Note:** If `DB_PASSWORD` is blank or `USE_SQLITE=True`, ShopSphere safely defaults to a local SQLite database for zero-friction setup and development.

### 4. Create MySQL Database (if using MySQL)
Open MySQL CLI or MySQL Workbench:
```sql
CREATE DATABASE shopsphere CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Apply Database Migrations
```bash
python manage.py makemigrations accounts catalog cart orders wishlist
python manage.py migrate
```

### 6. Seed Realistic Sample Data
Populate the database with 5 categories, 20 products with specifications, high-res SVG product images, active discount coupons, and ready-to-test accounts:
```bash
python manage.py seed_data
```

---

## 🔑 Default Demo Accounts

After running `python manage.py seed_data`, you can sign in with:

| Account Role | Username | Password | Email | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Customer** | `customer` | `Customer@123` | `alex@example.com` | Preloaded with addresses, order history, and reviews |
| **Admin / Staff** | `admin` | `Admin@123` | `admin@shopsphere.com` | Full administrative access to `/admin/` portal |

---

## 🎟️ Active Demo Coupons

| Coupon Code | Discount | Conditions |
| :--- | :--- | :--- |
| `WELCOME10` | **10% Off** | Minimum order: $50.00 (Max discount: $50) |
| `SAVE50` | **Flat $50 Off** | Minimum order: $300.00 |
| `FESTIVE25` | **25% Off** | Minimum order: $150.00 (Max discount: $100) |

---

## 🚀 Running the Application

Start Django's built-in ASGI/WSGI development server:
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Storefront:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Product Catalog:** [http://127.0.0.1:8000/products/](http://127.0.0.1:8000/products/)
- **Admin Dashboard:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Automated Testing Suite

ShopSphere includes an automated test suite with **24 unit and integration tests** covering user registration, authentication, search, catalog filtering, cart boundary validation, stock concurrency, atomic checkout, coupon rules, and permission isolation.

Run the test suite:
```bash
python manage.py test apps.accounts.tests apps.catalog.tests apps.cart.tests apps.orders.tests apps.wishlist.tests
```

Expected result:
```
Ran 24 tests in ~2.0s
OK
System check identified no issues (0 silenced).
```

---

## 🔒 Security Practices Implemented
1. **CSRF Protection:** All mutating requests (POST/PUT/DELETE) strictly enforce Django's CSRF token check.
2. **Strict Server-Side Computation:** Prices, cart subtotals, tax (5%), shipping tiers ($50 flat / free over $500), and coupon discounts are calculated on the server; client input prices are disregarded.
3. **Database Concurrency Protection:** Utilizes `transaction.atomic()` and `select_for_update()` during checkout to prevent race conditions on low-inventory items.
4. **Data Isolation:** Customers can only view and manage their own orders, cart, and addresses (`user=request.user` filter enforced in all protected views).
5. **Credential Protection:** Secrets and database connection credentials are fully decoupled into `.env` and kept out of version control.

---

## 🔮 Future Enhancements
- [ ] Integration of live payment gateways (Razorpay / Stripe Webhook Handlers)
- [ ] Automated email triggers via SendGrid or AWS SES for order confirmation PDFs
- [ ] Real-time courier tracking APIs (FedEx / Shiprocket)
- [ ] Redis caching layer for top-selling catalog queries and cart sessions

---

## 📄 License
This project is open-source and available under the **MIT License**.
Developed with pride by a Senior Full-Stack Software Engineer.
