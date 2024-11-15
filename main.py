import random
from email.mime.image import MIMEImage

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap5
from form import *
from werkzeug.utils import secure_filename
from functools import wraps
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from urllib.parse import urlparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import model
import datetime
import stripe
import math

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
stripe.api_key = os.getenv("STRIPE_KEY")
Bootstrap5(app)
db_connect = model.DBInit(app)

parsed_uri = urlparse(os.getenv("HOST_ADDRESS"))
current_host = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

DATE_NOW = datetime.datetime.now()


@login_manager.user_loader
def load_user(user_id):
    return db_connect.get_user_details(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        else:
            user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
            if user_access:
                return f(*args, **kwargs)
            else:
                return redirect(url_for('home'))

    return decorated_function


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', now=DATE_NOW), 404


@app.route("/", methods=["GET", "POST"])
def home():
    if 'cart' not in session:
        session['cart'] = db_connect.cart
        session['order'] = db_connect.order


    page = request.args.get('page', 1, type=int)
    per_page = db_connect.records_per_page
    offset = (page - 1) * per_page

    is_admin = False

    form = ProductSearchForm()
    categories = db_connect.get_product_categories()
    form.category.choices = [('0', 'All')]
    form.category.choices.extend([(categ.id, categ.name) for categ in categories])

    form_cart = AddtoCartForm()

    if current_user.is_authenticated:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if user_access:
            is_admin = True


    if 'search_home_criteria' not in session:
        session['search_home_criteria'] = {
                'keyword': "%%",
                'category': 0
        }

    search_criteria = session['search_home_criteria']
    if request.method == "POST":
        page=1
        search_criteria["keyword"] = f"%{form.keyword.data}%"
        search_criteria["category"] = form.category.data
        session['search_home_criteria'] = search_criteria
    else:
        if "search_home_criteria" in session:
            get_search_criteria = session['search_home_criteria']
            form.keyword.data = get_search_criteria["keyword"].replace("%","")
            form.category.data = get_search_criteria["category"]



    if int(search_criteria["category"]) > 0:
        products = db_connect.get_products(keyword=search_criteria["keyword"],limit=page,
                                       **{'status': 'ACTIVE', 'product_category_id': search_criteria["category"]})
    else:
        products = db_connect.get_products(keyword=search_criteria["keyword"],limit=page,
                                           **{'status': 'ACTIVE'})


    return render_template("home.html", products=products, form=form, form_cart=form_cart, is_admin=is_admin,
                           now=DATE_NOW)


@app.route("/about-us")
def about_us():
    is_admin = False
    if current_user.is_authenticated:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if user_access:
            is_admin = True

    return render_template("about_us.html", is_admin=is_admin, now=DATE_NOW)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        is_email_exist = db_connect.get_user(**{'email': email})
        if is_email_exist:
            flash("An account with the same email address has already signed up. Please login instead.", "error")
            return redirect(url_for("login"))
        else:
            encrypt_password = generate_password_hash(password, method="pbkdf2:sha256",
                                                      salt_length=8)
            new_user = model.User(
                email=email,
                password=encrypt_password,
                fname=form.fname.data,
                mname=form.mname.data,
                lname=form.lname.data,
                address=form.address.data,
                postal_code=form.postal_code.data,
                country=form.country.data,
                contact_no=form.contact_no.data

            )
            db_connect.add_user(new_user)
            flash("Welcome to Pastry Delight! Let's start shopping!", "success")

            user = db_connect.get_user(**{'email': email})
            login_user(user)
            return redirect(url_for("home"))
    return render_template("register.html", form=form, now=DATE_NOW)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():

            password = form.password.data
            user = db_connect.get_user(**{'email': form.email.data, 'status': 'ACTIVE'})
            if user:
                is_pwd_correct = check_password_hash(user.password, password)

                if is_pwd_correct:
                    login_user(user)
                    flash("Let's start shopping!", "success")
                    return redirect(url_for("home"))
                else:
                    flash("Incorrect login. Please check and try again.", "error")

            else:
                flash("We do not recognize this account. Please check and try again.", "error")

    return render_template("login.html", form=form, now=DATE_NOW)


@app.route('/logout')
@login_required
def logout():
    logout_user()

    if 'cart' in session:
        session.pop('cart')
        session.pop('order')

    flash("You are now logged out.", "success")
    return redirect(url_for('home'))


@app.route('/login/forgot_pass', methods=["GET", "POST"])
def forgot_pass():
    form = ForgotPassForm()

    if form.validate_on_submit():
        email = form.email.data
        user = db_connect.get_user(**{'email': email})
        if not user:
            flash('We do not recognize this account. Please check and try again.', 'error')
        else:
            flash('We have sent instructions to your email. Please check your inbox to login.', 'success')
            reset_password(user.id)

    return render_template("forgot_pass.html", form=form, now=DATE_NOW)


@app.route('/login/profile', methods=["GET", "POST"])
def profile():
    if not current_user.is_authenticated:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    form = ProfileForm()
    if request.method == "GET":
        form.lname.data = current_user.lname
        form.fname.data = current_user.fname
        form.mname.data = current_user.mname
        form.email.data = current_user.email
        form.contact_no.data = current_user.contact_no
        form.address.data = current_user.address
        form.postal_code.data = current_user.postal_code
        form.country.data = current_user.country

    if form.validate_on_submit():
        password = current_user.password
        if form.password.data != current_user.password:
            password = form.password.data

        encrypt_password = generate_password_hash(password, method="pbkdf2:sha256",
                                                  salt_length=8)
        details = model.User(
            lname=form.lname.data,
            fname=form.fname.data,
            mname=form.mname.data,
            email=form.email.data,
            contact_no=form.contact_no.data,
            address=form.address.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            password=encrypt_password
        )
        db_connect.update_user(current_user.id, details)
        flash("Profile changes saved succesfully.", 'success')

    return render_template("profile.html", form=form, now=DATE_NOW)


@app.route("/add_cart/<int:item_id>", methods=["GET", "POST"])
def add_cart(item_id):
    product_exist = db_connect.get_product(item_id)
    cart = session['cart']

    if not product_exist:
        flash("Invalid product!", "error")
    else:
        if request.method == "POST":

            new_item = {

                'id': item_id,
                'name': product_exist.name,
                'img_path': product_exist.img_path,
                'description': product_exist.description,
                'price': product_exist.price,
                'qty': int(request.form.get("qty"))
            }
            item_exists = next((item for item in cart if item["id"] == item_id), False)
            if item_exists:
                cart.remove(item_exists)

            cart.append(new_item)
            session['cart'] = cart

    return redirect(url_for('home'))


@app.route("/get_item/<int:item_id>", methods=["GET"])
def get_item(item_id):
    product_exist = db_connect.get_product(item_id)
    item_exists_in_cart = next((item for item in session['cart'] if item["id"] == item_id), False)

    details = {
        'name': product_exist.name,
        'img_path': product_exist.img_path,
        'description': product_exist.description,
        'price': product_exist.price,
        'qty': 0
    }
    if item_exists_in_cart:
        details = {
            'name': product_exist.name,
            'img_path': product_exist.img_path,
            'description': product_exist.description,
            'price': product_exist.price,
            'qty': item_exists_in_cart['qty']
        }

    return jsonify(details)


@app.route("/remove_item/<int:item_id>", methods=["GET"])
def remove_item(item_id):
    product_exist = db_connect.get_product(item_id)
    if not product_exist:
        flash("Invalid product!", "error")

    cart = session['cart']
    item_exists = next((item for item in cart if item["id"] == item_id), False)
    if item_exists:
        cart.remove(item_exists)
    else:
        flash("Item not in your cart!", "error")

    session['cart'] = cart
    return redirect(url_for('my_cart'))


def compute_total():
    order = session['order']
    cart = session['cart']
    subtotal = 0
    for item in cart:
        subtotal = subtotal + item['qty'] * item['price']

    order['subtotal'] = subtotal
    order['discount'] = (order['subtotal'] * (float(order['discount_percent'])) / 100)
    order['total'] = order['subtotal'] - order['discount']

    session['order'] = order
    session['cart'] = cart


@app.route("/apply_discount", methods=["GET", "POST"])
def apply_discount():
    code = request.args['discount_code']
    discount_exists = db_connect.get_discount_code(code)
    if discount_exists:
        session['order']['discount_code'] = code
        session['order']['discount_percent'] = discount_exists.value
    else:
        session['order']['discount_code'] = ""
        session['order']['discount'] = 0
        session['order']['discount_percent'] = 0

    compute_total()
    details = session['order']

    return jsonify(details)


@app.route("/my_cart", methods=["GET", "POST"])
def my_cart():
    is_admin = False
    if current_user.is_authenticated:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if user_access:
            is_admin = True

    if 'cart' not in session:
        session['cart'] = db_connect.cart
        session['order'] = db_connect.order

    cart = session["cart"]
    compute_total()

    if request.method == 'POST':

        for item in cart:
            item['qty'] = int(request.form.get("cart_item_qty" + str(item['id'])))

        discount_exists = db_connect.get_discount_code(request.form.get('discount_code'))

        if discount_exists:
            session['order']['discount_code'] = request.form.get('discount_code')
            session['order']['discount_percent'] = discount_exists.value
        else:
            session['order']['discount_code'] = ""
            session['order']['discount'] = 0
            session['order']['discount_percent'] = 0

        compute_total()
        return redirect(url_for('checkout'))

    order = session['order']

    return render_template("cart.html", cart=cart, is_admin=is_admin, order=order, now=DATE_NOW)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    if 'cart' not in session:
        flash('Please add items to your cart.', 'error')
        return redirect(url_for('my_cart'))
    cart = session["cart"]
    order = session["order"]
    user = db_connect.get_user_details(current_user.id)
    form = CheckoutForm()
    form.address.data = user.address
    if request.method == 'POST':
        now = datetime.datetime.now()
        order_num = now.strftime("%Y%m%d") + str(db_connect.count_orders_today() + 1)
        new_order = model.OrderHeader(
            order_num=order_num,
            order_by=current_user.lname + ", " + current_user.fname + " " + current_user.mname,
            address=current_user.address,
            postal_code=current_user.postal_code,
            country=current_user.country,
            subtotal=session['order']['subtotal'],
            total=session['order']['total'],
            discount_code=session['order']['discount_code'],
            discount_percent=session['order']['discount_percent'],
            discount_total=session['order']['discount'],
            status='PENDING PAYMENT',
            user_id=current_user.id
        )
        cart = session['cart']
        item_details = []
        for item in cart:
            sales_price = float(item['price']) * float(item['qty'])
            price_after_discount = sales_price

            line_discount = 0
            if line_discount > 0:
                price_after_discount = float(item['qty']) * (
                        float(item['price']) - (float(item['price']) * (line_discount / 100)))

            item_line = model.OrderLine(
                order_header_id=0,
                product_id=item['id'],
                product_name=item['name'],
                product_desc=item['description'],
                quantity=item['qty'],
                price=item['price'],
                line_price=sales_price,
                line_discount=line_discount,
                price_after_discount=price_after_discount,
                status='PENDING'
            )
            item_details.append(item_line)

        # INSERT DETAILS TO DATABASE
        new_order_id = db_connect.add_order(new_order, item_details)
        if new_order_id > 0:
            # REMOVE ITEMS IN CART AND ORDER DETAILS
            session.pop('order')
            session.pop('cart')

            # SEND ORDER NOTIF
            new_order_details = db_connect.get_order(new_order_id)
            html_content = mail_order_template(new_order_id)
            send_notif(current_user.email,
                       f"Pastry Delight: Order {new_order_details.order_num} - {new_order_details.status}",
                       html_content)

            # CREATE STRIPE SESSION
            stripe_resp = payment_api(new_order_id)
            if stripe_resp:
                db_connect.update_stripe_order(new_order_id, stripe_resp["id"])
                flash('Order successfully placed.', 'success')
                return redirect(stripe_resp["url"])

    return render_template("checkout.html", form=form, cart=cart, order=order, user=user, now=DATE_NOW)


def retrieve_payment_api(order_id):
    order = db_connect.get_order(order_id)
    try:
        stripe_response = stripe.checkout.Session.retrieve(
            order.stripe_session_id
        )
        return stripe_response

    except stripe.error.CardError as e:
        flash("A payment error occurred: {}".format(e.user_message), "error")
    except stripe.error.InvalidRequestError as e:
        flash(f"An invalid request occurred.{format(e.user_message)}", "error")
    except Exception as e:
        flash(f"Another problem occurred, maybe unrelated to Stripe.", "error")


def payment_api(order_id):
    order = db_connect.get_order(order_id)

    rate = db_connect.get_currency("USD")

    if not rate:
        flash("Currency not supported.", "error")
        return redirect(url_for('home'))

    total_amount = float(order.total) / float(rate.ph_value)
    try:
        unit_amount = math.ceil(round(total_amount, 2)) * 100
        new_price = stripe.Price.create(
            currency="USD",
            unit_amount=unit_amount,
            product_data={"name": "Order" + order.order_num},
        )

        success_url = f"{current_host}{url_for('checkout_success', order_id=order_id)}"
        r_url = f"{current_host}{url_for('order_list')}"
        stripe_response = stripe.checkout.Session.create(
            success_url=success_url,
            # return_url= r_url,
            # ui_mode="embedded",
            line_items=[{"price": new_price["id"], "quantity": 1}],
            mode="payment"
        )
        return stripe_response

    except stripe.error.CardError as e:
        flash("A payment error occurred: {}".format(e.user_message), "error")
    except stripe.error.InvalidRequestError as e:
        flash(f"An invalid request occurred.{format(e.user_message)}", "error")
    except Exception as e:
        flash(f"Another problem occurred, maybe unrelated to Stripe.", "error")


@app.route("/checkout_success/<int:order_id>", methods=["GET", "POST"])
def checkout_success(order_id):
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    order = db_connect.get_order(order_id)
    if not order:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order.user_id != current_user.id:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    db_connect.update_to_paid_order(order_id)
    flash('Order successfully paid.', 'success')

    html_content = mail_order_template(order_id)
    user = db_connect.get_user_details(order.user_id)
    send_notif(user.email, f"Pastry Delight: Order {order.order_num} - {order.status}", html_content)

    return redirect(url_for('order_list'))


# @app.route("/mail/<int:order_id>", methods=["GET", "POST"])
def mail_order_template(order_id):
    with open("templates/notif_order.html", 'r') as file:
        html_content = file.read()

    order = db_connect.get_order_view(order_id)

    html_content = html_content.replace("{{ order_num }}", order[0]['order_num'])
    html_content = html_content.replace("{{ order_status }}", order[0]['order_status'])
    html_content = html_content.replace("{{ order_by }}", order[0]['order_by'])
    html_content = html_content.replace("{{ address }}",
                                        order[0]['address'] + " " + order[0]['country'] + " " + order[0]['postal_code'])
    html_content = html_content.replace("{{ contact_no }}", order[0]['contact_no'])
    lines = ""
    for line in order:
        lines = lines + "<tr style='border-bottom:1px solid  #e5e5e5; '>"
        lines = lines + f"<td>{line['product_name']} <br/><span style='font-size:10px; color:#777'>{line['product_desc']}</span><br/><span style='font-size:12px'>{int(line['quantity'])}*{line['price']}</span></td>"
        lines = lines + f"<td style='text-align:right'>{line['line_price']}</td>"
        lines = lines + "</tr>"

    html_content = html_content.replace("{{ items }}", lines)
    html_content = html_content.replace("{{ subtotal }}", str(order[0]['subtotal']))
    html_content = html_content.replace("{{ discount_total }}", str(order[0]['discount_total']))
    html_content = html_content.replace("{{ total }}", str(order[0]['total']))

    return html_content


@app.route("/my_orders", methods=["GET", "POST"])
def order_list():
    if not current_user.is_authenticated:
        flash('Please log in first to see orders.', 'error')
        return redirect(url_for('login'))

    is_admin = False
    if current_user.is_authenticated:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if user_access:
            is_admin = True

    form = SearchForm()
    orders = db_connect.get_orders_by(current_user.id)

    if request.method == "POST":
        orders = db_connect.get_orders(keyword=form.keyword.data, **{'user_id': current_user.id})

    return render_template("orders.html", form=form, orders=orders, is_admin=is_admin, now=DATE_NOW)


@app.route("/my_orders/cancel/<int:order_id>", methods=["GET", "POST"])
def cancel_order(order_id):
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    order = db_connect.get_order(order_id)
    if not order:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order.user_id != current_user.id:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if not user_access:
            flash("Order is inaccessible! Let's add items to cart instead.", 'error')
            return redirect(url_for('order_list'))

    if order.status != 'PENDING PAYMENT':
        flash("Order cannot be cancelled with its current status.", 'error')
        return redirect(url_for('order_list'))

    db_connect.update_to_cancel_order(order_id)
    flash(f"Order #{order.order_num} successfully cancelled.", "success")

    html_content = mail_order_template(order_id)
    send_notif(current_user.email, f"Pastry Delight: Order {order.order_num} - {order.status}", html_content)
    return redirect(url_for('order_list'))


@app.route("/order_details/<int:order_id>", methods=["GET", "POST"])
def order_details(order_id):
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    is_admin = False
    if current_user.is_authenticated:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if user_access:
            is_admin = True

    order = db_connect.get_order_view(order_id)
    if not order:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order[0]['user_id'] != current_user.id:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if not user_access:
            flash("Order is inaccessible! Let's add items to cart instead.", 'error')
            return redirect(url_for('home'))

    return render_template("order_details.html", order=order, is_admin=is_admin, now=DATE_NOW)


@app.route("/open_stripe_link/<int:order_id>", methods=["GET", "POST"])
def open_stripe_link(order_id):
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    order = db_connect.get_order(order_id)
    if not order:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order.user_id != current_user.id:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order.status != 'PENDING PAYMENT':
        flash("Order is inaccessible! Please check and try again.", 'error')
        return redirect(url_for('order_list'))

    stripe_resp = retrieve_payment_api(order_id)
    if stripe_resp:
        if stripe_resp["url"]:
            db_connect.update_stripe_order(order_id, stripe_resp["id"])
            return redirect(stripe_resp["url"])
        else:
            db_connect.update_to_cancel_order(order_id)
            flash("Payment session expired. Please place a new order instead.", "error")
            return redirect(url_for('order_list'))
    else:
        flash("Unknown error occured.", "error")
        return redirect(url_for('order_list'))


@app.route("/admin_dashboard", methods=["GET", "POST"])
@admin_only
def admin_dashboard():
    if not current_user.is_authenticated:
        flash('Please log in first to see orders.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    new_users = len(db_connect.get_users(**{'status': 'ACTIVE'}))
    best_selling_products = db_connect.product_best_selling(5)
    paid_orders = len(db_connect.get_orders(keyword="", **{'status': 'PAID'}))
    data = {
        'new_users': new_users,
        'paid_orders': paid_orders,
        'best_selling': best_selling_products
    }

    return render_template("admin_dashboard.html", data=data, is_admin=True, now=DATE_NOW)


@app.route("/admin_order", methods=["GET", "POST"])
@admin_only
def admin_order():
    if not current_user.is_authenticated:
        flash('Please log in first to see orders.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    form = SearchForm()
    orders = db_connect.get_orders(keyword="")

    if request.method == "POST":
        orders = db_connect.get_orders(keyword=form.keyword.data)

    return render_template("admin_orders.html", form=form, orders=orders, is_admin=True, now=DATE_NOW)


@app.route("/admin_order_details/<int:order_id>", methods=["GET", "POST"])
def admin_order_details(order_id):
    if not current_user.is_authenticated:
        flash('Please log in first to place order.', 'error')
        return redirect(url_for('login'))

    order = db_connect.get_order_view(order_id)
    if not order:
        flash("Order is inaccessible! Let's add items to cart instead.", 'error')
        return redirect(url_for('home'))

    if order[0]['user_id'] != current_user.id:
        user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
        if not user_access:
            flash("Order is inaccessible! Let's add items to cart instead.", 'error')
            return redirect(url_for('home'))

    return render_template("admin_order_details.html", order=order, is_admin=True, now=DATE_NOW)


@app.route("/admin_product", methods=["GET", "POST"])
@admin_only
def admin_product():
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    form = ProductSearchForm()

    categories = db_connect.get_product_categories()
    form.category.choices = [('0', 'All')]
    form.category.choices.extend([(categ.id, categ.name) for categ in categories])


    if 'search_admin_product_criteria' not in session:
        session['search_admin_product_criteria'] = {
                'keyword': "%%",
                'category': 0
        }

    search_criteria = session['search_admin_product_criteria']
    if request.method == "POST":
        page=1
        search_criteria["keyword"] = f"%{form.keyword.data}%"
        search_criteria["category"] = form.category.data
        session['search_admin_product_criteria'] = search_criteria
    else:
        if "search_admin_product_criteria" in session:
            get_search_criteria = session['search_admin_product_criteria']
            form.keyword.data = get_search_criteria["keyword"].replace("%","")
            form.category.data = get_search_criteria["category"]



    if  search_criteria["keyword"] == "":
        search_criteria["keyword"] = f"%{ search_criteria["keyword"] }%"

    if int(search_criteria["category"]) > 0:
        where_cond = {
            'product_category_id': form.category.data
        }
        print("with where")
        products = db_connect.get_products(search_criteria["keyword"], limit=page,**where_cond)
    else:
        products = db_connect.get_products(search_criteria["keyword"],limit=page)



    return render_template("admin_products.html", products=products, form=form, is_admin=True, now=DATE_NOW)


@app.route("/admin_product_add", methods=["GET", "POST"])
@admin_only
def admin_product_add():
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    form = ProductForm()

    categories = db_connect.get_product_categories()
    form.category.choices = [(categ.id, categ.name) for categ in categories]

    if form.validate_on_submit():

        add_product = True
        product_exist = db_connect.get_product_details({'name': form.name.data})
        if product_exist:
            flash("Product with same name already exists!", "error")
            add_product = False

        product_exist = db_connect.get_product_details({'code': form.code.data})
        if product_exist:
            flash("Product with same code already exists!", "error")
            add_product = False

        if add_product:

            details = model.Product(
                name=form.name.data,
                code=form.code.data,
                description=form.description.data,
                product_category_id=form.category.data,
                remarks=form.remarks.data,
                price=form.price.data,
                created_by=current_user
            )
            db_connect.add_product(details)

            product_added = db_connect.get_product_details({'name': form.name.data})
            if product_added:
                if form.filename.data:
                    filename = secure_filename(form.filename.data.filename)
                    # save to product images folder
                    img_ext = filename.split('.')
                    new_file_name = str(product_added.id) + "." + img_ext[-1]
                    file_path = 'static/images/products/' + new_file_name
                    form.filename.data.save(file_path)

                    db_connect.update_product({'img_path': new_file_name}, product_added.id)

            flash("Product added successfully!", "success")
            return redirect(url_for('admin_product'))
    return render_template("admin_products_form.html", form=form, is_admin=True, now=DATE_NOW)


@app.route("/admin_product_update/<int:product_id>", methods=["GET", "POST"])
@admin_only
def admin_product_update(product_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    form = ProductForm()

    product = db_connect.get_product(product_id)
    if not product:
        flash('Invalid product!', 'error')
        return redirect(url_for('admin_product'))

    categories = db_connect.get_product_categories()
    form.category.choices = [(categ.id, categ.name) for categ in categories]
    if request.method == 'GET':
        form.name.data = product.name
        form.code.data = product.code
        form.description.data = product.description
        form.remarks.data = product.remarks
        form.price.data = product.price
        form.filename.data = product.img_path
        form.category.data = str(product.product_category_id)

    if form.validate_on_submit():

        product_exist = db_connect.get_product_details({'name': form.name.data})
        if product_exist:
            if product_exist.id != product.id:
                flash("Product with same name already exists!", "error")

        new_file_name = ""
        if form.filename.data.filename:
            filename = secure_filename(form.filename.data.filename)
            # save to product images folder
            img_ext = filename.split('.')
            new_file_name = str(product.id) + "." + img_ext[-1]
            file_path = 'static/images/products/' + new_file_name
            form.filename.data.save(file_path)

        if new_file_name == "":
            new_file_name = product.img_path

        update_details = {
            'name': form.name.data,
            'code': form.code.data,
            'description': form.description.data,
            'product_category_id': form.category.data,
            'remarks': form.remarks.data,
            'price': form.price.data,
            'img_path': new_file_name
        }

        db_connect.update_product(update_details, product_id)

        flash("Product updated successfully!", "success")
        return redirect(url_for('admin_product'))
    return render_template("admin_products_form.html", form=form, product=product, is_admin=True, now=DATE_NOW)


@app.route("/admin_product_status/<int:product_id>", methods=["GET", "POST"])
@admin_only
def admin_product_status(product_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    product_exist = db_connect.get_product(product_id)
    if product_exist:
        db_connect.product_change_stat(product_id)
        flash("Product status changed!", "success")
    else:
        flash("Invalid product!", "error")
    return redirect(url_for('admin_product'))


@app.route("/admin_prodcategory", methods=["GET", "POST"])
@admin_only
def admin_product_category():
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    form = SearchForm()
    new_form = NewDescriptionForm()

    categories = db_connect.get_product_category_by(keyword="")
    if form.validate_on_submit():

        keyword = f"%{form.keyword.data}%"

        categories = db_connect.get_product_category_by(keyword)
        if len(categories) == 0:
            flash("Category not found.", "error")
    return render_template("admin_products_category.html", categories=categories, form=form, new_form=new_form,
                           is_admin=True, now=DATE_NOW)


@app.route("/admin_prodcategory_status/<int:category_id>", methods=["GET", "POST"])
@admin_only
def admin_product_category_status(category_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show categories.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Categories inaccessible.", 'error')
        return redirect(url_for('home'))

    categ_exist = db_connect.get_product_category(category_id)
    if categ_exist:
        new_status = 'ACTIVE'
        if categ_exist.status == 'ACTIVE':
            new_status = 'INACTIVE'
        db_connect.product_category_change_stat(category_id)
        flash(f"Category status changed to {new_status}!", "success")
    else:
        flash("Invalid category!", "error")
    return redirect(url_for('admin_product_category'))


@app.route("/admin_product/category_add", methods=["GET", "POST"])
@admin_only
def admin_product_category_add():
    if not current_user.is_authenticated:
        flash('Please log in first to view categories.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product category is inaccessible.", 'error')
        return redirect(url_for('home'))

    form = NewDescriptionForm()

    if form.validate_on_submit():

        add_product = True
        categ_exist = db_connect.get_product_category_name(form.description.data)
        if categ_exist:
            flash("Category with same description already exists!", "error")
            add_product = False

        if add_product:

            db_connect.add_category({'name': form.description.data})

            categ_added = db_connect.get_product_category_name(form.description.data)
            if categ_added:
                flash("Product added successfully!", "success")
    return redirect(url_for('admin_product_category'))


@app.route("/admin_prodcategory_update/<int:category_id>", methods=["GET", "POST"])
@admin_only
def admin_product_category_update(category_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show categories.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Categories inaccessible.", 'error')
        return redirect(url_for('home'))

    categ_exist = db_connect.get_product_category(category_id)
    if categ_exist:

        form = NewDescriptionForm()

        if form.validate_on_submit():
            details = {
                'name': form.description.data
            }
            description_exists = db_connect.get_product_category_name(form.description.data)
            if description_exists:
                flash(f"Category with same description already exists!", "error")
            else:
                db_connect.update_product_category(details, category_id)
                flash(f"Category updated!", "success")
    else:
        flash("Invalid category!", "error")
    return redirect(url_for('admin_product_category'))


@app.route("/admin_get_category_json/<int:category_id>", methods=["GET"])
def admin_get_category_json(category_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show categories.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Categories inaccessible.", 'error')
        return redirect(url_for('home'))

    categ_exist = db_connect.get_product_category(category_id)

    details = {
        'name': categ_exist.name,
        'status': categ_exist.status,
    }

    return jsonify(details)


@app.route("/admin_user", methods=["GET", "POST"])
@admin_only
def admin_user():
    form = SearchForm()
    users = db_connect.get_users_by(keyword="")

    if form.validate_on_submit():
        keyword = f"%{form.keyword.data}%"
        users = db_connect.get_users_by(keyword)
        if len(users) == 0:
            flash("User not found.", "error")

    return render_template("admin_users.html", users=users, form=form, is_admin=True, now=DATE_NOW)


@app.route("/admin_user_status/<int:user_id>", methods=["GET", "POST"])
@admin_only
def admin_user_status(user_id):
    if not current_user.is_authenticated:
        flash('Please log in first to show products.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("Product catalog inaccessible.", 'error')
        return redirect(url_for('home'))

    user_exist = db_connect.get_user_details(user_id)
    if user_exist:
        db_connect.user_change_stat(user_id)
        flash("User status updated!", "success")
    else:
        flash("Invalid user!", "error")
    return redirect(url_for('admin_user'))


@app.route("/admin_user_resetpass/<int:user_id>", methods=["GET", "POST"])
@admin_only
def admin_user_resetpass(user_id):
    if not current_user.is_authenticated:
        flash('Please log in first to reset password.', 'error')
        return redirect(url_for('login'))

    user_access = db_connect.get_user_access(**{'user_id': current_user.id, 'user_group_id': 1})
    if not user_access:
        flash("User inaccessible.", 'error')
        return redirect(url_for('home'))

    flash("Reset password success! New password has been sent to user's email address. ", "success")
    reset_password(user_id)

    return redirect(url_for('admin_user'))


def reset_password(user_id):
    user_exist = db_connect.get_user_details(user_id)
    if not user_exist:
        flash("Invalid user!", "error")
    else:

        random_password = generate_password()
        encrypt_password = generate_password_hash(random_password, method="pbkdf2:sha256",
                                                  salt_length=8)
        db_connect.update_user(user_id, model.User(password=encrypt_password))

        with open("templates/notif_reset_pass.html", 'r') as file:
            html_content = file.read()

        html_content = html_content.replace("[name]", user_exist.fname)
        html_content = html_content.replace("[new_password]", random_password)
        html_content = html_content.replace("{{ login_url }}", current_host + url_for('login'))
        send_notif(user_exist.email, "Pastry Delight: Password Reset", html_content)


def generate_password():
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
               'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

    nr_letters = random.randint(4, 6)
    nr_symbols = random.randint(2, 4)
    nr_numbers = random.randint(2, 4)

    password_letters = [random.choice(letters) for letter in range(nr_letters)]
    password_symbols = [random.choice(letters) for symbol in range(nr_symbols)]
    password_numbers = [random.choice(numbers) for num in range(nr_numbers)]

    password_list = password_letters + password_symbols + password_numbers

    random.shuffle(password_list)

    password = "".join(password_list)
    return password


def send_notif(send_to, subject, html_content):
    # Create a multipart message
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = os.getenv('GMAIL_EMAIL')
    msg["To"] = send_to

    # Attach the HTML content to the message
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    # Open and attach the image file
    with open('static/images/pd_horizontal.png', 'rb') as img_file:
        img = MIMEImage(img_file.read())
        img.add_header('Content-ID', '<image1>')  # Content-ID to reference the image in HTML
        msg.attach(img)

    with smtplib.SMTP(os.getenv("GMAIL_SMTP")) as connection:
        connection.starttls()
        connection.login(user=os.getenv('GMAIL_EMAIL'), password=os.getenv('GMAIL_PASSKEY'))
        connection.sendmail(from_addr=os.getenv('GMAIL_EMAIL'), to_addrs=send_to,
                            msg=msg.as_string())


if __name__ == '__main__':
    app.run(debug=True, port=5001)
