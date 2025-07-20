# ShopFusion Django Backend API

A comprehensive Django REST API backend for the ShopFusion e-commerce platform with features including user authentication, product management, shopping cart, orders, and more.

## Features

### Authentication & User Management

- Custom user model with email-based authentication
- OTP verification for registration and password reset
- User profile management
- Address and payment method management
- HTTP-only cookie-based sessions

### Products & Catalog

- Product categories and subcategories
- Product variants (color, size, material)
- Product images and galleries
- Product reviews and ratings
- Wishlist functionality
- Advanced filtering and search

### Shopping & Orders

- Shopping cart management
- Order processing and tracking
- Promo code system
- Order history and status tracking
- Inventory management

### API Features

- RESTful API design
- Comprehensive filtering and pagination
- Health check endpoint
- CORS support for frontend integration
- Detailed error handling

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd django-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (SQLite for development, PostgreSQL for production)
DB_NAME=shopfusion_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis for OTP storage
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 4. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/verify-otp/` - OTP verification
- `POST /api/auth/forgot-password/` - Forgot password
- `POST /api/auth/reset-password/` - Reset password
- `GET/PUT /api/auth/profile/` - User profile

### User Management

- `GET/POST /api/auth/addresses/` - User addresses
- `GET/POST /api/auth/payment-methods/` - Payment methods

### Products

- `GET /api/products/products/` - List products
- `GET /api/products/products/{id}/` - Product details
- `GET /api/products/products/featured/` - Featured products
- `GET /api/products/categories/` - Product categories
- `GET /api/products/search/` - Search products

### Shopping Cart

- `GET /api/orders/cart/` - Get cart
- `GET/POST /api/orders/cart/items/` - Cart items
- `PUT /api/orders/cart/items/{id}/` - Update cart item
- `DELETE /api/orders/cart/items/{id}/` - Remove cart item

### Orders

- `GET/POST /api/orders/orders/` - List/Create orders
- `GET /api/orders/orders/{id}/` - Order details
- `POST /api/orders/orders/{id}/cancel/` - Cancel order
- `POST /api/orders/promo-code/validate/` - Validate promo code

### System

- `GET /api/health/` - Health check

## Frontend Integration

This API is designed to work with the React frontend. Update your frontend API configuration:

```javascript
// In your frontend .env file
VITE_API_BASE_URL=http://localhost:8000
```

The API supports:

- HTTP-only cookies for authentication
- CORS for cross-origin requests
- CSRF protection
- Comprehensive error responses

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t shopfusion-backend .

# Run container
docker run -p 8000:8000 shopfusion-backend
```

### Environment Variables for Production

Update your production `.env`:

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
SECRET_KEY=your-production-secret-key

# PostgreSQL database
DB_NAME=shopfusion_prod
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=your_db_host
DB_PORT=5432

# Redis
REDIS_URL=redis://your-redis-host:6379/0

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

## Sample Data

The API includes fixtures for sample data:

```bash
# Load sample categories and products
python manage.py loaddata fixtures/categories.json
python manage.py loaddata fixtures/products.json
```

## API Documentation

Once the server is running, you can explore the API:

- Admin interface: `http://localhost:8000/admin/`
- API root: `http://localhost:8000/api/`
- Health check: `http://localhost:8000/api/health/`

## Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test apps.accounts
python manage.py test apps.products
python manage.py test apps.orders
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.
