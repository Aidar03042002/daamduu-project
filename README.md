# Daamduu - Restaurant Menu Management System

A modern web application for managing restaurant menus, handling payments, and providing QR code-based menu access.

## Features

- 🍽️ Menu Management
  - Create and manage menu items
  - Upload and manage food images
  - Set prices and descriptions
  - Weekly menu planning

- 💳 Payment Integration
  - Secure Stripe payment processing
  - Payment status tracking
  - Transaction history

- 📱 QR Code System
  - Generate QR codes for menu items
  - Mobile-friendly menu display
  - Quick access to payment

- 👥 User Management
  - User registration and authentication
  - Role-based access control
  - Profile management

- 📊 Admin Dashboard
  - Sales analytics
  - Menu performance tracking
  - User management

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL
- **Cache**: Redis
- **Payment**: Stripe
- **Monitoring**: Prometheus, Grafana
- **Testing**: pytest, Locust
- **CI/CD**: GitHub Actions

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Node.js (for development)
- Stripe account

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/daamduu.git
cd daamduu
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

## Development

### Running Tests
```bash
pytest
```

### Running Performance Tests
```bash
locust
```

### Code Quality
```bash
flake8
black .
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Monitoring

The application includes:
- Prometheus metrics
- Grafana dashboards
- Performance monitoring
- Error tracking

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django community
- Stripe for payment processing
- All contributors and users

## Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter)
Project Link: [https://github.com/your-username/daamduu](https://github.com/your-username/daamduu) 