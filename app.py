from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

# ❌ si variable absente (local)
if not database_url:
    print("⚠️ DATABASE_URL non trouvée (mode local)")
    database_url = "postgresql://user:password@host:5432/dbname"  # temporaire

# Render fix
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/")
def home():
    try:
        db.session.execute(text("SELECT 1"))
        return "Connexion PostgreSQL OK ✅"
    except Exception as e:
        return f"Erreur ❌ {e}"

if __name__ == "__main__":
    app.run(debug=True)