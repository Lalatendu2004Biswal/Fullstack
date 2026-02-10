from flask import Flask, render_template, redirect, url_for, request, session
import pymysql
from config import config

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

def get_db_connection():
    # This function would typically return a database connection
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DATABASE'],
        port=app.config['MYSQL_PORT']
    )

@app.route("/")
def home():
    return render_template("start.html")

@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if username exists
        cur.execute("SELECT id FROM users WHERE username=%s", (u,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return render_template("register.html", msg="User already exists!")
        
        # Insert new user
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (u, p))
            conn.commit()  # Must commit to save changes
            return redirect(url_for("login"))
        except Exception as e:
            return f"Error: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch user details
        cur.execute("SELECT username, password FROM users WHERE username=%s", (u,))
        user_record = cur.fetchone()
        
        cur.close()
        conn.close()

        # Check if user exists and password matches
        if user_record and user_record[1] == p:
            session["user"] = u
            return redirect(url_for("dashboard"))

        return render_template("login.html", msg="Invalid login!")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)