# Django Authentication System

A production-ready authentication system built with Django 5.0+, featuring email-based authentication, email verification, password reset, and user profile management.

## Features

- **Email-Based Authentication** — Login using email instead of username
- **User Registration** — Secure registration with email verification
- **Email Verification** — Signed activation links with expiring tokens
- **Password Reset** — Complete password reset workflow via email
- **User Profiles** — One-to-one profiles with avatar, bio, and timestamps
- **Session Security** — Remember-me option, secure session handling
- **Protected Routes** — Login-required decorators and mixins
- **Responsive UI** — Clean, accessible templates with custom CSS
- **Comprehensive Testing** — 40+ tests covering models, forms, views, and flows

## Tech Stack

| Component          | Technology                           |
| ------------------ | ------------------------------------ |
| Framework          | Django 5.0                           |
| Python             | 3.11+                                |
| Database           | SQLite (development)                 |
| Authentication     | Django built-in auth system          |
| Email              | SMTP / Console backend               |
| Image Processing   | Pillow                               |

## Project Structure

```
authentication_project/
├── accounts/                  # Main authentication app
│   ├── migrations/            # Database migrations
│   ├── templates/accounts/    # Account templates
│   │   └── emails/            # Email templates
│   ├── admin.py               # Admin configuration
│   ├── apps.py                # App configuration
│   ├── forms.py               # Form classes
│   ├── managers.py            # Custom user manager
│   ├── models.py              # CustomUser + UserProfile
│   ├── services.py            # Business logic (email sending)
│   ├── signals.py             # Signal handlers
│   ├── tests.py               # Test suite
│   ├── tokens.py              # Email verification tokens
│   ├── urls.py                # URL routing
│   └── views.py               # View functions and classes
├── authentication_project/    # Project configuration
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── templates/                 # Project-level templates
│   ├── base.html              # Base template
│   └── includes/              # Reusable template parts
├── static/                    # Static files (CSS, JS)
├── media/                     # Uploaded user content
├── .env.example               # Environment variable template
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Quick Start

### 1. Clone and set up

```bash
git clone <repository-url>
cd authentication_project
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` to suit your environment. For local development, the defaults work out of the box:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

### 8. Visit the application

Open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Email Configuration

### Development

By default, emails are printed to the console:

```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production (SMTP)

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

## Running Tests

Run the full test suite:

```bash
python manage.py test accounts
```

Run with verbose output:

```bash
python manage.py test accounts --verbosity 2
```

The test suite includes:

| Test Category         | Tests                                      |
| --------------------- | ------------------------------------------ |
| Model tests           | User creation, profile auto-creation       |
| Form tests            | Registration validation, login validation  |
| Token tests           | Token generation, validation, expiry       |
| View tests            | Registration flow, activation, login/logout|
| Integration tests     | Full registration-to-dashboard flow        |
| Security tests        | CSRF, password hashing, session invalidation|

## API Routes

| URL Pattern                            | Description                  | Auth Required |
| -------------------------------------- | ---------------------------- | ------------- |
| `/accounts/register/`                  | User registration            | No            |
| `/accounts/login/`                     | Login                        | No            |
| `/accounts/logout/`                    | Logout                       | No            |
| `/accounts/activate/<uid>/<token>/`    | Email verification           | No            |
| `/accounts/password-reset/`            | Request password reset       | No            |
| `/accounts/profile/`                   | View/edit profile            | Yes           |
| `/accounts/dashboard/`                 | User dashboard               | Yes           |
| `/accounts/account-settings/`          | Account settings             | Yes           |
| `/admin/`                              | Django admin                 | Staff         |

## Security Features

- **CSRF Protection** — Enabled on all forms
- **Password Hashing** — PBKDF2 with SHA-256 (default)
- **Password Validation** — Django's built-in validators (length, complexity, common password checks)
- **Session Security** — HTTP-only cookies, secure in production
- **Input Validation** — All user input validated through Django forms
- **XSS Prevention** — Django templates auto-escape variables
- **Secure Redirects** — No open redirect vulnerabilities
- **Rate Limiting Ready** — Prepared for addition of rate limiting middleware
- **Environment Variables** — No hardcoded secrets
- **Signed Tokens** — Django's PasswordResetTokenGenerator for email verification

## Customization

### Changing the User Model

The `CustomUser` model is defined in `accounts/models.py`. To add fields:

1. Add the field to the model
2. Create and run a migration
3. Update the form and admin as needed

### Adding Profile Fields

The `UserProfile` model has a one-to-one relationship with `CustomUser`.
Add fields to `accounts/models.py.UserProfile` and migrate.

### Styling

All CSS is in `static/css/styles.css`. The design uses CSS custom properties
for easy theming — just update the `:root` variables.

## License

MIT
