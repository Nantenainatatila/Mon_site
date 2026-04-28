
from flask import Flask,render_template,redirect,request,session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import flash

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret_key"

# 🔥 récupérer DATABASE_URL
database_url = os.getenv("DATABASE_URL")

# ❌ si pas trouvé → erreur claire (pas fallback dangereux)
if not database_url:
    raise Exception("DATABASE_URL manquante sur Render ❌")

# 🔧 fix Render (postgres → postgresql)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



#"""database_url = os.getenv("DATABASE_URL")

#if not database_url:
#    print("⚠️ Mode local activé")
#    database_url = "sqlite:///db_teste"

#app.config['SQLALCHEMY_DATABASE_URI'] = database_url
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#db = SQLAlchemy(app)
#"""

# TABLE USER
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    role = db.Column(db.String(50))
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    password = db.Column(db.String(200))


# TABLE PRODUIT
class Produit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    description = db.Column(db.Text)
    prix = db.Column(db.Float)
    reactions = db.Column(db.Integer)

class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'))

    # empêche un user de liker 2 fois le même produit
    __table_args__ = (db.UniqueConstraint('user_id', 'produit_id'),)

# TABLE COMMANDE
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

    return "Produit ajouté avec succès ✅"

@app.route("/like/<int:produit_id>")
def like(produit_id):

    user_id = session.get('user_id')

    if not user_id:
        return "Connectez-vous pour liker ❌"

    exist = Likes.query.filter_by(
        user_id=user_id,
        produit_id=produit_id
    ).first()

    if not exist:
        new_like = Likes(user_id=user_id, produit_id=produit_id)
        db.session.add(new_like)

        produit = Produit.query.get(produit_id)
        produit.reactions = (produit.reactions or 0) + 1

        db.session.commit()

    # afficher produits
    produits = Produit.query.all()

    max_likes = db.session.query(db.func.max(Produit.reactions)).scalar()

    best_produits = Produit.query.filter(
        Produit.reactions == max_likes
    ).all()

    return render_template('index.html',produits=produits,best_produits=best_produits,max_likes=max_likes)
    

@app.route("/apropos/<int:produit_id>")
def apropos(produit_id):

    produit = Produit.query.get_or_404(produit_id)

    return render_template("apropos.html", produit=produit)


@app.route("/", methods=["GET","POST"])
def home():
    message2 = ""
    if request.method == "POST":

        nom = request.form['nom']
        password = request.form['password']

        # chercher utilisateur
        user = User.query.filter_by(nom=nom).first()

        if user and check_password_hash(user.password, password):

        # stocker session
            session['user_id'] = user.id
            session['role'] = user.role

            # 🔁 redirection selon rôle
            if user.role == "admin":
                 return redirect('/admin')
            else:
                return redirect('/index')
        else:
            message2 = "Nom ou mot de passe incorrect ❌"
            return render_template("connexion.html",message2=message2)
    return render_template("connexion.html")
@app.route("/index")
def index():
    produits = Produit.query.all()
    max_likes = db.session.query(db.func.max(Produit.reactions)).scalar()

    # 🔥 2. récupérer tous les produits avec ce max
    best_produits = Produit.query.filter(Produit.reactions == max_likes).all()
    return render_template("index.html", produits=produits, best_produits=best_produits, max_likes=max_likes)

@app.route("/creercompte", methods= ["GET", "POST"])
def creercompte():
   
    if request.method == "POST":
        nom = request.form.get('nom')
        role = request.form.get('role')
        adresse = request.form.get('adresse')
        telephone = request.form.get('telephone')
        password = request.form.get('password')

        # 🔐 sécuriser le mot de passe
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



    

@app.route("/commande/<int:produit_id>", methods=["GET","POST"])
def commande(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    if request.method == "POST":

        nombre = (request.form.get('nombre_produit'))

        if not nombre:
            return "Quantité invalide ❌"

        nombre = int(nombre)
        user_id = session.get('user_id')

        produit = Produit.query.get(produit_id)

        if not produit:
            return "Produit introuvable ❌"

        prix_total = produit.prix * nombre

        new_cmd = Commande(
            user_id=user_id,
            produit_id=produit.id,
            nombre_produit=nombre,
            prix_total_produit=prix_total
        )

        db.session.add(new_cmd)
        db.session.commit()

        flash("Commande envoyée ")
    return render_template("commande.html",produit=produit)

@app.route("/admin")
def admin():
        if session.get('role') != "admin":
            return "Accès refusé ❌"

        commandes = Commande.query.all()

        return render_template("admin.html", commandes=commandes)
    


@app.route("/logout")
def logout():
    session.clear() 
    return redirect("/")



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
