from flask import Flask, render_template, request, redirect, url_for
import pymysql
from Config import config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user,login_required, logout_user, current_user
import datetime
from functools import wraps

app = Flask(__name__)
app.config.from_object(config)
#for providing better security to the session we use flask_login
#LoginManager main object
red = LoginManager()
red.init_app(app)
red.login_view = "login"  # If not logged in, redirect here


def get_db_connection():
    return pymysql.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"],
        port=app.config["MYSQL_PORT"]
    )


def init_db():
    """Create/alter tables for course management and admin."""
    conn = get_db_connection()
    cur = conn.cursor()

  
    try:
        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'
            """
        )
    except pymysql.err.OperationalError:
       
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

   
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS course_packages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            duration_months INT,
            price_inr DECIMAL(10,2) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
        """
    )

   
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            course_id INT NOT NULL,
            package_id INT NOT NULL,
            amount_inr DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) NOT NULL,
            razorpay_payment_id VARCHAR(100),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES course_packages(id) ON DELETE CASCADE
        )
        """
    )

  
    cur.execute("SELECT COUNT(*) FROM courses")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute(
            "INSERT INTO courses (title, description, created_at) VALUES (%s, %s, %s)",
            ("Python for Beginners", "Start your Python journey from zero.", datetime.datetime.now()),
        )
        course_id = cur.lastrowid

        packages = [
            ("3 Months Access", 3, 999.00),
            ("6 Months Access", 6, 1499.00),
            ("1 Year Access", 12, 2499.00),
            ("Unlimited Access", None, 3999.00),
        ]
        for name, duration, price in packages:
            cur.execute(
                "INSERT INTO course_packages (course_id, name, duration_months, price_inr, created_at) VALUES (%s, %s, %s, %s, %s)",
                (course_id, name, duration, price, datetime.datetime.now()),
            )

    conn.commit()
    cur.close()
    conn.close()


def get_courses_with_packages():
    """Return courses with their packages for display."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute("SELECT * FROM courses ORDER BY created_at DESC")
    courses = cur.fetchall()

    cur.execute(
        "SELECT * FROM course_packages ORDER BY course_id, price_inr ASC"
    )
    packages = cur.fetchall()

    by_course = {}
    for p in packages:
        by_course.setdefault(p["course_id"], []).append(p)
    for c in courses:
        c["packages"] = by_course.get(c["id"], [])

    cur.close()
    conn.close()
    return courses


# usermixing  -  is a class whixh gives this (means this particular database)  
# User model default methods required by flask_login :

# is_authenticated

# is_active

# is_anonymous

# get_id()

# Your User Class
# The class that you use to represent users needs to implement these properties and methods:

# is_authenticated
# This property should return True if the user is authenticated, i.e. they have provided valid credentials. (Only authenticated users will fulfill the criteria of login_required.)

# is_active
# This property should return True if this is an active user - in addition to being authenticated, they also have activated their account, not been suspended, or any condition your application has for rejecting an account. Inactive accounts may not log in (without being forced of course).

# is_anonymous
# This property should return True if this is an anonymous user. (Actual users should return False instead.)

# get_id()
# This method must return a str that uniquely identifies this user, and can be used to load the user from the user_loader callback. Note that this must be a str - if the ID is natively an int or some other type, you will need to convert it to str.

class User(UserMixin):#inheritence UserMixin is  parent class here we did  it use all the methods of resp. class
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


#for laoding user in a session 
@red.user_loader  #red object belongs to flask_login
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return User(user[0], user[1], user[2]) # user[0]  → first column → id
                                               # user[1]  → second column → username
                                               # user[2]  → role
    return None



@app.route("/")
def home():
    return redirect(url_for("index"))


@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

  
        role = "admin" if u == "admin" else "user"

        hashed_password = generate_password_hash(p)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=%s", (u,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return render_template("register.html", msg="User already exists!")

        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (u, hashed_password, role)
        )
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, username, password, role FROM users WHERE username=%s",
            (u,)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2], p):
            user_obj = User(user[0], user[1], user[3])
            login_user(user_obj)  
            if user_obj.is_admin:
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))

        return render_template("login.html", msg="Invalid username or password!")

    return render_template("login.html")


@app.route("/dashboard")
@login_required  #wrapper funtion of flask_login manager to verify user 
def dashboard():
   
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    courses = get_courses_with_packages()
    return render_template("dashboard.html", user=current_user.username, courses=courses)


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return "Forbidden", 403
        return f(*args, **kwargs)
    return wrapper
#done till this part

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Simple admin dashboard with overview numbers."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(amount_inr), 0) FROM orders")
    total_revenue = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        user=current_user.username,
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
    )


@app.route("/courses")
@login_required
def courses():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    courses = get_courses_with_packages()
    return render_template("courses.html", user=current_user.username, courses=courses)


@app.route("/purchase/<int:package_id>", methods=["GET", "POST"])#here id suggets pakage id ie. 1,2,3 
@login_required
def purchase(package_id):
    """Demo Razorpay-like purchase flow (no real API call)."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(
        """
        SELECT p.id AS package_id, p.name, p.duration_months, p.price_inr,
               c.id AS course_id, c.title AS course_title
        FROM course_packages p
        JOIN courses c ON c.id = p.course_id
        WHERE p.id = %s
        """,
        (package_id,),
    )
    pkg = cur.fetchone()

    if not pkg:
        cur.close()
        conn.close()
        return "Package not found", 404

    if request.method == "POST":
      
        cur.execute(
            """
            INSERT INTO orders (user_id, course_id, package_id, amount_inr, status, razorpay_payment_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                current_user.id,
                pkg["course_id"],
                pkg["package_id"],
                pkg["price_inr"],
                "paid",  # demo: mark as paid directly
                "DEMO_PAYMENT",  # demo Razorpay payment id
                datetime.datetime.now(),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("my_purchases"))

    cur.close()
    conn.close()
    return render_template("purchase.html", user=current_user.username, pkg=pkg)


@app.route("/my-purchases")
@login_required
def my_purchases():
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(
        """
        SELECT o.id, o.amount_inr, o.status, o.created_at,
               c.title AS course_title,
               p.name AS package_name
        FROM orders o
        JOIN courses c ON c.id = o.course_id
        JOIN course_packages p ON p.id = o.package_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
        """,
        (current_user.id,),
    )
    orders = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("my_purchases.html", user=current_user.username, orders=orders)


@app.route("/admin/users")
@admin_required
def admin_users():
    """List all users and how many orders they have."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(
        """
        SELECT u.id, u.username, u.role, COUNT(o.id) AS order_count
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id
        GROUP BY u.id, u.username, u.role
        ORDER BY u.id
        """
    )
    users = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    """Delete a user and all their orders (via FK cascade)."""
    if user_id == current_user.id:
        return "You cannot delete yourself.", 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_users"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    """List all orders with user and course details."""
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(
        """
        SELECT o.id, o.amount_inr, o.status, o.created_at,
               u.username,
               c.title AS course_title,
               p.name AS package_name
        FROM orders o
        JOIN users u ON u.id = o.user_id
        JOIN courses c ON c.id = o.course_id
        JOIN course_packages p ON p.id = o.package_id
        ORDER BY o.created_at DESC
        """
    )
    orders = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/orders/<int:order_id>/delete", methods=["POST"])
@admin_required
def admin_delete_order(order_id):
    """Delete a specific order."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE id=%s", (order_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_orders"))


@app.route("/admin/courses/new", methods=["GET", "POST"])
@admin_required
def admin_add_course():
    """Admin: add a new course with standard packages."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            return render_template("admin_add_course.html", msg="Title is required")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO courses (title, description, created_at) VALUES (%s, %s, %s)",
            (title, description or None, datetime.datetime.now()),
        )
        course_id = cur.lastrowid

        packages = [
            ("3 Months Access", 3, 999.00),
            ("6 Months Access", 6, 1499.00),
            ("1 Year Access", 12, 2499.00),
            ("Unlimited Access", None, 3999.00),
        ]
        for name, duration, price in packages:
            cur.execute(
                "INSERT INTO course_packages (course_id, name, duration_months, price_inr, created_at) VALUES (%s, %s, %s, %s, %s)",
                (course_id, name, duration, price, datetime.datetime.now()),
            )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_add_course.html")


@app.route("/logout")
@login_required
def logout():#previously  we use session pop or session clear 
    logout_user()   # Proper logout   previously we used to pop user from a session. which manaully removes user from session this is better
    return redirect(url_for("login"))


if __name__ == "__main__":
    
    init_db()
    app.run(debug=True)