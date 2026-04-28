from flask import Flask, render_template, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ✅ Clé secrète depuis variable d'environnement
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key_change_in_prod")

# ✅ Récupérer DATABASE_URL depuis l'environnement
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise Exception("DATABASE_URL manquante sur Render ❌")

# ✅ Fix Render (postgres:// → postgresql://)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ─── MODÈLES ──────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50))
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    password = db.Column(db.String(200))


class Produit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    description = db.Column(db.Text)
    prix = db.Column(db.Float)
    reactions = db.Column(db.Integer, default=0)


class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'))
    __table_args__ = (db.UniqueConstraint('user_id', 'produit_id'),)


class Commande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'))
    produit = db.relationship('Produit')
    nombre_produit = db.Column(db.Integer)
    prix_total_produit = db.Column(db.Float)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/add_produit")
def add_produit():
    produits = [
        Produit(nom="Téléphone Samsung", description="Android 128GB", prix=250000, reactions=0),
        Produit(nom="iPhone 13", description="Apple smartphone", prix=450000, reactions=0),
        Produit(nom="Casque Bluetooth", description="Sans fil", prix=50000, reactions=0),
        Produit(nom="Clavier gamer", description="RGB mécanique", prix=80000, reactions=0),
    ]
    db.session.add_all(produits)
    db.session.commit()
    return "Produits ajoutés avec succès ✅"


@app.route("/like/<int:produit_id>")
def like(produit_id):
    user_id = session.get('user_id')

    if not user_id:
        flash("Connectez-vous pour liker ❌")
        return redirect('/')

    exist = Likes.query.filter_by(user_id=user_id, produit_id=produit_id).first()

    if not exist:
        new_like = Likes(user_id=user_id, produit_id=produit_id)
        db.session.add(new_like)

        produit = db.session.get(Produit, produit_id)
        if produit:
            produit.reactions = (produit.reactions or 0) + 1
        db.session.commit()

    return redirect('/index')  # ✅ redirect au lieu de render_template


@app.route("/apropos/<int:produit_id>")
def apropos(produit_id):
    produit = db.session.get(Produit, produit_id)
    if not produit:
        return "Produit introuvable ❌", 404
    return render_template("apropos.html", produit=produit)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nom = request.form['nom']
        password = request.form['password']

        user = User.query.filter_by(nom=nom).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == "admin":
                return redirect('/admin')
            else:
                return redirect('/index')
        else:
            flash("Nom ou mot de passe incorrect ❌")
            return render_template("connexion.html")

    return render_template("connexion.html")


@app.route("/index")
def index():
    produits = Produit.query.all()
    max_likes = db.session.query(db.func.max(Produit.reactions)).scalar()
    best_produits = Produit.query.filter(Produit.reactions == max_likes).all()
    return render_template("index.html", produits=produits, best_produits=best_produits, max_likes=max_likes)


@app.route("/creercompte", methods=["GET", "POST"])
def creercompte():
    if request.method == "POST":
        nom = request.form.get('nom')
        role = request.form.get('role')
        adresse = request.form.get('adresse')
        telephone = request.form.get('telephone')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password)

        user_exist = User.query.filter_by(nom=nom).first()

        if user_exist:
            flash("❌ Ce nom existe déjà !")
            return redirect('/creercompte')
        else:
            new_user = User(
                nom=nom,
                role=role,
                adresse=adresse,
                telephone=telephone,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Création succès ✅")
            return redirect('/')

    return render_template("creercompte.html")


@app.route("/commande/<int:produit_id>", methods=["GET", "POST"])
def commande(produit_id):
    # ✅ db.session.get() remplace .get_or_404() déprécié
    produit = db.session.get(Produit, produit_id)
    if not produit:
        return "Produit introuvable ❌", 404

    if request.method == "POST":
        nombre = request.form.get('nombre_produit')

        if not nombre:
            flash("Quantité invalide ❌")
            return render_template("commande.html", produit=produit)

        nombre = int(nombre)
        user_id = session.get('user_id')

        if not user_id:
            flash("Connectez-vous pour commander ❌")
            return redirect('/')

        prix_total = produit.prix * nombre

        new_cmd = Commande(
            user_id=user_id,
            produit_id=produit.id,
            nombre_produit=nombre,
            prix_total_produit=prix_total
        )
        db.session.add(new_cmd)
        db.session.commit()
        flash("Commande envoyée ✅")

    return render_template("commande.html", produit=produit)


@app.route("/admin")
def admin():
    if session.get('role') != "admin":
        return "Accès refusé ❌", 403

    commandes = Commande.query.all()
    return render_template("admin.html", commandes=commandes)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")