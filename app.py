from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")


print("DATABASE_URL =", os.getenv("DATABASE_URL"))

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
    
    return render_template("/index.html")
if __name__ == "__main__":
    app.run(debug=True)