Course Management System

A full-stack Flask-based e-commerce platform designed for selling and managing online courses. This system allows individuals to list courses and browse, purchase, and access learning materials.

```Project Structure:
Fullstack/
├── templates/              # Jinja2 HTML templates for the frontend
│   ├── dashboard.html      # User and instructor control panel
│   ├── div3.html           # Modular UI component
│   ├── home.html           # Authenticated user landing page
│   ├── index.html          # Public marketplace storefront
│   ├── login.html          # Secure user login page
│   ├── register.html       # New user account registration
│   └── start.html          # Initial entry or onboarding page
├── veer/                   # Core application logic and modules
├── config.py               # Application configuration settings
└── demo.py                 # Main entry point to run the Flask server
```
🛠️ Installation & Setup

Follow these steps to set up the project locally on your machine.
```
**Clone the repository**
  git clone https://github.com/Lalatendu2004Biswal/Fullstack.git

**Create a Virtual Environment and activate the VM**
  python -m venv veer
  veer/scripts/activate   

**Run the code**
  python demo.py
```
Tech Stack
```
**Backend**
  Framework: Flask (Python)
  Database: MySQL (managed via MySQL Workbench)
  ORM: Flask-SQLAlchemy for database modeling
  Database Driver: PyMySQL to connect Python with MySQL

**Frontend**
  Templates: Jinja2 for dynamic HTML rendering
  Styling: HTML5 and CSS3
  Interactivity: JavaScript
```
