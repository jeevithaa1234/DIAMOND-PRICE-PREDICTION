import os
import pickle
import pandas as pd
import csv
import sqlite3
from math import sqrt
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps

from config import Config
from database import create_tables, get_connection


# ==============================
# Load ML Model
# ==============================

with open("diamond.pkl", "rb") as f:
    model = pickle.load(f)

with open("label_encoders.pkl", "rb") as f:
    label_encoders = pickle.load(f)


# ==============================
# Flask App
# ==============================

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

create_tables()


# ==============================
# Login Required Decorator
# ==============================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user" not in session:

            flash("Please login first.", "warning")

            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


# ==============================
# Home Pages
# ==============================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ==============================
# Register
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:

            flash("Passwords do not match.", "danger")

            return redirect("/register")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            conn.close()

            flash("Email already exists.", "warning")

            return redirect("/register")

        hashed = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(?,?,?)
            """,
            (name, email, hashed)
        )

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect("/login")

    return render_template("register.html")


# ==============================
# Login
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user"] = user["name"]
            session["email"] = user["email"]

            flash("Login Successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password.", "danger")

    return render_template("login.html")


# ==============================
# Logout
# ==============================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect("/")


# ==============================
# Dashboard
# ==============================

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ==============================
# Prediction
# ==============================

@app.route("/prediction", methods=["GET", "POST"])
@login_required
def prediction():

    if request.method == "POST":

        try:

            # Numeric Features
            carat = float(request.form["carat"])
            depth = float(request.form["depth"])
            table = float(request.form["table"])
            x = float(request.form["x"])
            y = float(request.form["y"])
            z = float(request.form["z"])

            # Categorical Features
            cut = request.form["cut"]
            color = request.form["color"]
            clarity = request.form["clarity"]

            # Encode Categories
            cut_encoded = label_encoders["cut"].transform([cut])[0]
            color_encoded = label_encoders["color"].transform([color])[0]
            clarity_encoded = label_encoders["clarity"].transform([clarity])[0]

            # Arrange Features
            features = pd.DataFrame([{

                "carat": carat,
                "cut": cut_encoded,
                "color": color_encoded,
                "clarity": clarity_encoded,
                "depth": depth,
                "table": table,
                "x": x,
                "y": y,
                "z": z

            }])

            # Predict
            predicted_price = round(
                float(model.predict(features)[0]),
                2
            )

            # Save Prediction
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO prediction_history
                (
                    user_email,
                    carat,
                    cut,
                    color,
                    clarity,
                    depth,
                    table_value,
                    x,
                    y,
                    z,
                    predicted_price
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session["email"],
                carat,
                cut,
                color,
                clarity,
                depth,
                table,
                x,
                y,
                z,
                predicted_price
            ))

            conn.commit()
            conn.close()

            return render_template(
                "result.html",
                prediction=predicted_price,
                carat=carat,
                cut=cut,
                color=color,
                clarity=clarity
            )

        except Exception as e:

            flash(f"Prediction Error: {e}", "danger")

            return redirect("/prediction")

    return render_template("prediction.html")


# ==============================
# Result Page
# ==============================

@app.route("/result")
@login_required
def result():
    return render_template("result.html")

# ==============================
# Prediction History
# ==============================

@app.route("/history")
@login_required
def history():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM prediction_history
        WHERE user_email=?
        ORDER BY prediction_date DESC
    """, (session["email"],))

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history
    )


# ==============================
# Delete Prediction
# ==============================

@app.route("/delete_prediction/<int:id>")
@login_required
def delete_prediction(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM prediction_history
        WHERE id=? AND user_email=?
    """, (id, session["email"]))

    conn.commit()
    conn.close()

    flash("Prediction deleted successfully.", "success")

    return redirect("/history")


# ==============================
# Export Prediction History
# ==============================

@app.route("/export_history")
@login_required
def export_history():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM prediction_history
        WHERE user_email=?
        ORDER BY prediction_date DESC
    """, (session["email"],))

    rows = cursor.fetchall()

    conn.close()

    def generate():

        yield "ID,Date,Carat,Cut,Color,Clarity,Depth,Table,X,Y,Z,Predicted Price\n"

        for row in rows:

            yield (
                f'{row["id"]},'
                f'{row["prediction_date"]},'
                f'{row["carat"]},'
                f'{row["cut"]},'
                f'{row["color"]},'
                f'{row["clarity"]},'
                f'{row["depth"]},'
                f'{row["table_value"]},'
                f'{row["x"]},'
                f'{row["y"]},'
                f'{row["z"]},'
                f'{row["predicted_price"]}\n'
            )

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=prediction_history.csv"
        }
    )


# ==============================
# Statistics
# ==============================

@app.route("/statistics")
@login_required
def statistics():

    dataset_path = os.path.join(
        app.root_path,
        "dataset",
        "diamonds.csv"
    )

    df = pd.read_csv(dataset_path)

    # Value counts
    cut_counts = df["cut"].value_counts()
    color_counts = df["color"].value_counts()
    clarity_counts = df["clarity"].value_counts()

    stats = {

        "total_records": int(len(df)),

        "average_price": float(round(df["price"].mean(), 2)),

        "highest_price": int(df["price"].max()),

        "lowest_price": int(df["price"].min()),

        "average_carat": float(round(df["carat"].mean(), 2)),

        "average_depth": float(round(df["depth"].mean(), 2)),

        "cut_labels": [str(x) for x in cut_counts.index.tolist()],
        "cut_values": [int(x) for x in cut_counts.tolist()],

        "color_labels": [str(x) for x in color_counts.index.tolist()],
        "color_values": [int(x) for x in color_counts.tolist()],

        "clarity_labels": [str(x) for x in clarity_counts.index.tolist()],
        "clarity_values": [int(x) for x in clarity_counts.tolist()]
    }

    preview = df.head(10).to_dict(orient="records")

    return render_template(
        "statistics.html",
        stats=stats,
        preview=preview
    )


# ==============================
# Feature Importance
# ==============================

@app.route("/feature_importance")
@login_required
def feature_importance():

    features = [
        "Carat",
        "Cut",
        "Color",
        "Clarity",
        "Depth",
        "Table",
        "X",
        "Y",
        "Z"
    ]

    importances = model.feature_importances_

    feature_data = sorted(
        zip(features, importances),
        key=lambda x: x[1],
        reverse=True
    )

    labels = [item[0] for item in feature_data]
    values = [round(float(item[1]), 4) for item in feature_data]

    return render_template(
        "feature_importance.html",
        labels=labels,
        values=values,
        feature_data=feature_data
    )


# ==============================
# Compare Diamonds
# ==============================

@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():

    result = None

    if request.method == "POST":

        diamond1 = [
            float(request.form["carat1"]),
            label_encoders["cut"].transform([request.form["cut1"]])[0],
            label_encoders["color"].transform([request.form["color1"]])[0],
            label_encoders["clarity"].transform([request.form["clarity1"]])[0],
            float(request.form["depth1"]),
            float(request.form["table1"]),
            float(request.form["x1"]),
            float(request.form["y1"]),
            float(request.form["z1"])
        ]

        diamond2 = [
            float(request.form["carat2"]),
            label_encoders["cut"].transform([request.form["cut2"]])[0],
            label_encoders["color"].transform([request.form["color2"]])[0],
            label_encoders["clarity"].transform([request.form["clarity2"]])[0],
            float(request.form["depth2"]),
            float(request.form["table2"]),
            float(request.form["x2"]),
            float(request.form["y2"]),
            float(request.form["z2"])
        ]

        price1 = model.predict([diamond1])[0]
        price2 = model.predict([diamond2])[0]

        if price1 > price2:
            better = "Diamond 1"
        elif price2 > price1:
            better = "Diamond 2"
        else:
            better = "Both diamonds have approximately the same predicted price."

        result = {
            "price1": round(price1, 2),
            "price2": round(price2, 2),
            "better": better
        }

    return render_template("compare.html", result=result)


# ==============================
# Profile
# ==============================

@app.route("/profile")
@login_required
def profile():

    conn = sqlite3.connect("diamond.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Logged-in user details
    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (session["email"],)
    )
    user = cursor.fetchone()

    # Total predictions
    cursor.execute(
        "SELECT COUNT(*) FROM prediction_history WHERE user_email = ?",
        (session["email"],)
    )
    total_predictions = cursor.fetchone()[0]

    # Prediction statistics
    cursor.execute("""
        SELECT
            AVG(predicted_price),
            MAX(predicted_price),
            MIN(predicted_price)
        FROM prediction_history
        WHERE user_email = ?
    """, (session["email"],))

    stats = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        total_predictions=total_predictions,
        average_price=round(stats[0], 2) if stats[0] else 0,
        highest_price=round(stats[1], 2) if stats[1] else 0,
        lowest_price=round(stats[2], 2) if stats[2] else 0
    )

# ==============================
# Feedback
# ==============================

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():

    if request.method == "POST":

        rating = request.form["rating"]
        comments = request.form["comments"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback(user_email, rating, comments)
            VALUES(?,?,?)
        """, (
            session["email"],
            rating,
            comments
        ))

        conn.commit()
        conn.close()

        flash("Thank you for your feedback!", "success")

        return redirect("/feedback")

    return render_template("feedback.html")


# ==============================
# Contact
# ==============================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contact_messages
            (name, email, subject, message)
            VALUES(?,?,?,?)
        """, (
            name,
            email,
            subject,
            message
        ))

        conn.commit()
        conn.close()

        flash("Message sent successfully!", "success")

        return redirect("/contact")

    return render_template("contact.html")


@app.route("/model_performance")
@login_required
def model_performance():

    metrics = {
        "model": "Random Forest Regressor",
        "r2": round(0.9709432155772922, 4),
        "mae": round(360.1338877880853, 2),
        "mse": round(461910.5139155275, 2),
        "rmse": round(sqrt(461910.5139155275), 2)
    }

    return render_template(
        "model_performance.html",
        metrics=metrics
    )

@app.route("/dataset")
@login_required
def dataset():

    dataset_path = os.path.join(
        app.root_path,
        "dataset",
        "diamonds.csv"
    )

    df = pd.read_csv(dataset_path)

    dataset_info = {
        "rows": len(df),
        "columns": len(df.columns),
        "target": "price",
        "missing": int(df.isnull().sum().sum())
    }

    preview = df.head(10).to_dict(orient="records")

    return render_template(
        "dataset.html",
        dataset_info=dataset_info,
        columns=df.columns,
        preview=preview
    )

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/report")
@login_required
def report():

    conn = sqlite3.connect("diamond.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM prediction_history
        WHERE user_email = ?
        ORDER BY prediction_date DESC
        LIMIT 1
    """, (session["email"],))

    prediction = cursor.fetchone()

    conn.close()

    return render_template(
        "report.html",
        prediction=prediction
    )

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html"), 500
# ==============================
# Run App
# ==============================

if __name__ == "__main__":
    app.run(debug=True)