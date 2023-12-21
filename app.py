from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, Blueprint, render_template, request, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from Db import db
from Db.models import User, Product
from flask_login import UserMixin
from flask_login import login_user, login_required, current_user, logout_user



app = Flask(__name__)


app.secret_key = '123'
user_db = "trubitsyna"
host_ip = "localhost"
host_port = "5433"
database_name = "trubitsyna_rgz"
password = "123"


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db.init_app(app)


login_manager=LoginManager()
login_manager.login_view = 'app.login'
login_manager.init_app(app)
@login_manager.user_loader
def load_users(user_id):
    return User.query.get(int(user_id))

@app.route("/rgz")
def main():
    if current_user.is_authenticated:
        # если пользователь авторизирован
        visibleUser = current_user.username
        
    else:
        # если пользователь не авторизирован
        visibleUser = 'Anon'
    products = Product.query.all()
    return render_template('rgz.html', username=visibleUser, products=products)


@app.route('/rgz/log', methods=["GET","POST"])
def loginPage():
    errors = []

    if request.method == "GET":
        return render_template("log.html", errors=errors)
    
    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        errors = ["Пожалуйста, заполните все поля"]
        return render_template("log.html", errors=errors)
    
    my_user=User.query.filter_by(username=username).first()

    hashPassword = generate_password_hash(password, method='pbkdf2')
    if not check_password_hash(my_user.password, password):
        errors = 'Введен неправильный пароль'
        return render_template('log.html', errors=errors)
    

    
    if my_user is not None:
        if check_password_hash(my_user.password, password):
            #Сохраняем JWT токен
            login_user(my_user,remember=False)
            return redirect('/rgz')
    return redirect('/rgz/log')

@app.route('/rgz/register', methods=["GET","POST"])
def registerPage():
    errors = []

    if request.method == "GET":
        return render_template("register.html", errors=errors)
    
    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        return render_template("register.html", errors="Пожалуйста, заполните все поля")
    if len(password) < 5:
        return render_template("register.html", errors="Пароль меньше 5-ти символов")

    my_user=User.query.filter_by(username=username).first()

    if my_user is not None:
        errors='Пользователь с данным именем уже существует'
        return render_template('register.html',errors=errors)

    hashedPswd = generate_password_hash(password, method='pbkdf2')
    newUser = User(username=username,password=hashedPswd)

    db.session.add(newUser)
    db.session.commit()

    return redirect("/rgz/log")

@app.route('/main/delete', methods=['POST'])
@login_required
def delete():
    user_id = current_user.id
    user = users.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return redirect('/login')

@app.route("/rgz/delete_user", methods=["POST"])
@login_required
def delete_user():
    user_id = current_user.id
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return redirect('/log')