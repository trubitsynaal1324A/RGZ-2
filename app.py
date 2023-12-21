from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, Blueprint, render_template, request, make_response, redirect, url_for, session, abort
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

    hashedPassword = generate_password_hash(password, method='pbkdf2')
    newUser = User(username=username,password=hashedPassword)

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
    return redirect('rgz/log')

@app.route('/rgz/logout')
def logout():
    logout_user() 
    return redirect('/rgz/log')

@app.route('/rgz/korzina')
def cart():
    cart_items = request.form.get("cart_items", [])
    cart_total = request.form.get("cart_total", 0)

    return render_template("korzina.html", cart_items=cart_items, cart_total=cart_total)

@app.route('/rgz/add_to_cart', methods=["POST"])
def add_to_cart():
        if not session.get ("username"):
            abort(403)

        product_ids = request.form.getlist("product_id")
        kolvo = request.form.getlist("kolvo")

        if not (product_ids and kolvo):
            abort(400)

        cart_items = session.get("cart_items",[])
        cart_total = session.get("cart_total",0 ) # Переменная для хранения общей суммы

        for product_id, kolvo in zip(product_ids, kolvo):
            product = Product.query.filter_by(id=product_id).first()

            if product:
                available_kolvo = product.kolvo
                requested_kolvo = int(kolvo)
                if available_kolvo >= requested_kolvo:
                    cart_items.append({"name": product.name, "price": product.price, "kolvo": kolvo})
                    cart_total += int(product.price) * requested_kolvo

                else:
                    cart_items.append({"name": product.name , "price": product.price , "quantity": available_kolvo})
                    cart_total += int(product.price) * available_kolvo

        session["cart_items"] = cart_items
        session["cart_total"] = cart_total

        return render_template("korzina.html", cart_items=cart_items, cart_total=cart_total)
        

@app.route('/rgz/remove_from_cart', methods=["POST"])
def remove_from_cart():
    if not session.get("username"):
        abort(403)

    product.name = request.form.get("product.name")
    product.price = (request.form.get("product.price").replace(",","."))
    product.kolvo = request.form.get("product.kolvo")

    if not (product.name and product.price and product.kolvo):
        abort(400)
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    updated_cart_items = []
    for item in cart_items:
        if item["name"] != product.name or item["price"] != product.price or item["kolvo"] != product.kolvo:
            updated_cart_items.append(item)
            price = item["price"].replace(",", ".")  
            cart_total += float(price) * int(item["kolvo"]) 

    session["cart_items"] = updated_cart_items
    session["cart_total"] = cart_total 

    
    return redirect("/rgz/korzina")

@app.route('/rgz/oplata', methods=["GET", "POST"])
def oplata():
    if not session.get("username"):
        return redirect('/rgz/log')  # Перенаправление на страницу входа

    if request.method == "POST":
        # Получить данные карты из формы
        card_num = request.form.get("card_num")
        cvv = request.form.get("cvv")

        # Проверить данные карты
        if len(card_num) != 16:
            print('Неверный номер карты. Пожалуйста, введите 16-значный номер карты.', 'error')
            return redirect('/rgz/oplata')
        
        if len(cvv) != 3:
            print('Неверный CVV. Пожалуйста, введите 3-значный CVV код.', 'error')
            return redirect('/rgz/oplata')

        # Очистка корзины после оплаты
        session.pop("cart_items", None)
        session.pop("cart_total", None)

        return render_template('success.html')
    
    # Вывести информацию о корзине и форму оплаты
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    return render_template("oplata.html", cart_items=cart_items, cart_total=cart_total)
