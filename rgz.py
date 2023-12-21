from flask import Blueprint, request, render_template, redirect, url_for, abort, jsonify, session
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2 import extras


rgz = Blueprint ("rgz", __name__)

def dbConnect():
    conn = psycopg2.connect(
        host="localhost", 
        database="trubitsyna_rgz",
        user="trubitsyna",
        password="123")
    
    return conn

def dbClose(cur,conn):
    cur.close()
    conn.close()


@rgz.route("/rgz")
def main():
    conn = dbConnect()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    
    cur.execute("SELECT * FROM product")
    products = cur.fetchall()
    
    username = session.get("username")
    
    if not username:
        visibleUser = "Anon"
        return render_template('rgz.html', username=visibleUser, products=products)
    return render_template('rgz.html', username=username, products=products)


@rgz.route('/rgz/register', methods=["GET","POST"])
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

    hashPassword = generate_password_hash(password)

    conn = dbConnect() 
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE username = %s", (username,))

    if cur.fetchone() is not None:
        errors = ["Пользователь с данным именем уже существует"]
        dbClose(cur,conn)
        return render_template("register.html", errors=errors)
    
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashPassword))

    conn.commit()
    conn.close()
    cur.close()

    return redirect("/rgz/log")

@rgz.route('/rgz/log', methods=["GET","POST"])
def loginPage():
    errors = []

    if request.method == "GET":
        return render_template("log.html", errors=errors)
    
    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        errors = ["Пожалуйста, заполните все поля"]
        return render_template("log.html", errors=errors)

    conn = dbConnect() 
    cur = conn.cursor()

    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))

    result = cur.fetchone()

    if result is None:
        errors = ["Неправильный логин или пароль"]
        dbClose(cur,conn)
        return render_template("log.html", errors=errors)
    
    userID, hashPassword = result

    if check_password_hash(hashPassword, password):
        session['id'] = userID
        session['username'] = username
        dbClose(cur,conn)
        return redirect("/rgz")
    else:
        errors = ["Неправильный логин или пароль"]
        return render_template("log.html", errors=errors)

@rgz.route("/rgz/delete_user", methods=["POST"])
def delete_user():
    if not session.get("username"):
        abort(403)

    # Получение идентификатора пользователя, которого нужно удалить
    user_id = session.get("id")

    # Удаление пользователя из базы данных
    conn = dbConnect()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    cur.close()

    # Очистка сессии
    session.clear()

    return redirect("/rgz/log")
   
@rgz.route('/rgz/logout')
def logout():
    session.clear()  
    return redirect('/rgz/log')

@rgz.route('/rgz/add_to_cart', methods=["POST"])
def add_to_cart():
    if not session.get("username"):
        abort(403)

    product_ids = request.form.getlist("product_id")
    kolvo = request.form.getlist("kolvo")

    if not product_ids or not kolvo:
        abort(400)

    conn = dbConnect()
    cur = conn.cursor(cursor_factory=extras.DictCursor)

    cart_items = session.get("cart_items") or []
    cart_total = session.get("cart_total") or 0  # Переменная для хранения общей суммы

    for product_id, kolvo in zip(product_ids, kolvo):
        cur.execute("SELECT name_, price, kolvo FROM product WHERE id = %s", (product_id,))
        product = cur.fetchone()

        if product:
            available_kolvo = product["kolvo"]
            if available_kolvo >= int(kolvo):
                cart_items.append({"name": product["name_"], "price": product["price"], "kolvo": kolvo})
                cart_total += int(product["price"]) * int(kolvo)

            else:
                cart_items.append({"name": product["name_"], "price": product["price"], "kolvo": available_kolvo})
                cart_total += int(product["price"]) * int(available_kolvo)

    conn.close()
    cur.close()
    session["cart_items"] = cart_items
    session["cart_total"] = cart_total

    return render_template("korzina.html", cart_items=cart_items, cart_total=cart_total)


@rgz.route('/rgz/korzina')
def cart():
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    return render_template("korzina.html", cart_items=cart_items, cart_total=cart_total)

@rgz.route('/rgz/remove_from_cart', methods=["POST"])
def remove_from_cart():
    if not session.get("username"):
        abort(403)

    product_name = request.form.get("product_name")
    product_price = request.form.get("product_price")
    product_kolvo = request.form.get("product_kolvo")

    if not (product_name and product_price and product_kolvo):
        abort(400)
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    updated_cart_items = []
    for item in cart_items:
        if item["name"] != product_name or item["price"] != product_price or item["kolvo"] != product_kolvo:
            updated_cart_items.append(item)
            price = item["price"].replace(",", ".")  
            cart_total += float(price) * int(item["kolvo"]) 

    session["cart_items"] = updated_cart_items
    session["cart_total"] = cart_total 

    
    return redirect("/rgz/korzina")


@rgz.route('/rgz/oplata', methods=["GET", "POST"])
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