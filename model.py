from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.sql import func, collate
from flask_login import UserMixin
from sqlalchemy import or_, and_, text, engine
from datetime import datetime


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fname: Mapped[str] = mapped_column(String(100), nullable=False)
    mname: Mapped[str] = mapped_column(String(100), nullable=False)
    lname: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_no: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(250), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    # children: Mapped[list["OrderHeader"]] = relationship()
    status: Mapped[str] = mapped_column(String(20))
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    orders = relationship("OrderHeader", back_populates="created_by")
    products = relationship("Product", back_populates="created_by")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class UserGroup(db.Model):
    __tablename__ = "user_group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class UserAccess(db.Model):
    __tablename__ = "user_access"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_group_id: Mapped[int] = mapped_column(ForeignKey("user_group.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    modified_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Product(db.Model):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=True, unique=True)
    price: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    remarks: Mapped[str] = mapped_column(String(250), nullable=True)
    status: Mapped[str] = mapped_column(String(100))
    img_path: Mapped[str] = mapped_column(String(250), nullable=True)
    product_category_id: Mapped[int] = mapped_column(ForeignKey("product_category.id"))
    product_category = relationship("ProductCategory", back_populates="products")
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_by = relationship("User", back_populates="products")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class ProductCategory(db.Model):
    __tablename__ = "product_category"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250))
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(100))
    products = relationship("Product", back_populates="product_category")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class OrderHeader(db.Model):
    __tablename__ = "order_header"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_num: Mapped[str] = mapped_column(String(20))
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    order_by: Mapped[str] = mapped_column(String(250), nullable=False)
    address: Mapped[str] = mapped_column(String(250), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_code: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_total: Mapped[float] = mapped_column(Float)
    discount_percent: Mapped[float] = mapped_column(Float)
    subtotal: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(100))
    stripe_session_id: Mapped[str] = mapped_column(String(250), nullable=True)
    paid_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)
    completion_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_by = relationship("User", back_populates="orders")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class OrderLine(db.Model):
    __tablename__ = "order_line"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_header_id: Mapped[int] = mapped_column(ForeignKey("order_header.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product_name: Mapped[str] = mapped_column(String(250))
    product_desc: Mapped[str] = mapped_column(String(250))
    quantity: Mapped[int] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    line_price: Mapped[float] = mapped_column(Float)
    line_discount: Mapped[float] = mapped_column(Float, nullable=True)
    price_after_discount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(100))

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Discount(db.Model):
    __tablename__ = "discount"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    value: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class ExchangeRate(db.Model):
    __tablename__ = "exchange_rate"
    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(20))
    currency_code: Mapped[str] = mapped_column(String(25))
    ph_value: Mapped[float] = mapped_column(Float)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class DBInit():
    def __init__(self, app):
        self.app = app
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
        self.db = db
        self.cart = []
        self.order = {
            'subtotal': 0,
            'discount': 0,
            'discount_percent': 0,
            'discount_code': '',
            'total': 0
        }
        self.db.init_app(self.app)
        self.create_table()

    def create_table(self):
        with self.app.app_context():
            self.db.create_all()
            product_categories = self.get_product_categories()
            user_groups = self.get_user_group()
            currency = self.get_currency("USD")
            discount = self.get_discounts()
            user_access = self.get_user_access()
            if len(product_categories) == 0:
                self.add_category({'name': 'Default'})
            if len(user_groups) == 0:
                self.add_user_group(UserGroup(name='ADMIN'))
                self.add_user_group(UserGroup(name='CUSTOMER'))
            if not currency:
                self.add_currency(ExchangeRate(country_code="US", currency_code="USD", ph_value=56, user_id=1))
            if not discount:
                self.add_discount(Discount(code="TEN", value=10, status="ACTIVE", user_id=1))
            if not user_access:
                self.add_user_access(UserAccess(user_group_id=1, user_id=1, modified_by=1))

    def execute_query(self, query):
        # SQL query to create the view
        view_creation_query = query

        # Execute the SQL query using SQLAlchemy's engine
        with self.app.app_context():
            with db.engine.connect() as connection:
                connection.execute(text(view_creation_query))

    ##PRODUCTS
    def get_products(self, keyword, **where_cond):
        if where_cond:
            if keyword != "":

                keyword = f"%{keyword}%"
                record_list = Product.query.filter_by(**where_cond).where(
                    or_(Product.name.like(keyword), Product.code.like(keyword), Product.description.like(keyword),
                        Product.remarks.like(keyword))).order_by(Product.name.asc()).all()
            else:

                record_list = Product.query.filter_by(**where_cond).order_by(Product.name.asc()).all()

        else:
            record_list = self.db.session.execute(
                db.select(Product).order_by(collate(Product.name, 'NOCASE'))).scalars().all()
        return record_list

    def get_product_details(self, where_cond):
        record = Product.query.filter_by(**where_cond).order_by(Product.name.asc()).scalar()

        return record

    def get_product(self, id):
        record = self.db.session.execute(db.select(Product).where(Product.id == id).order_by(Product.name)).scalar()
        return record

    def add_product(self, details: Product):
        with self.app.app_context():
            details.status = 'ACTIVE'
            self.db.session.add(details)
            self.db.session.commit()

    def update_product(self, details, product_id):
        product_update = self.get_product(product_id)
        if 'name' in details:
            product_update.name = details['name']
            product_update.code = details['code']
            product_update.description = details['description']
            product_update.product_category_id = details['product_category_id']
            product_update.remarks = details['remarks']
            product_update.price = details['price']
        product_update.img_path = details['img_path']
        self.db.session.commit()

    def product_change_stat(self, product_id):
        product_update = self.get_product(product_id)
        if product_update.status == "ACTIVE":
            product_update.status = "DEACTIVATED"
        else:
            product_update.status = "ACTIVE"
        self.db.session.commit()

    def product_best_selling(self, limit):
        query = """
            SELECT order_line.product_id , product.code,order_line.product_desc, 
            SUM(order_line.quantity) as total_qty
            FROM order_line
            INNER JOIN order_header 
            on order_header.id == order_line.order_header_id
            INNER JOIN product
            on product.id == order_line.product_id
            WHERE order_header.status = 'PAID'
            GROUP BY product_id,product.code, product_desc
            ORDER BY  SUM(order_line.quantity) DESC
        """
        limit = f" LIMIT {limit}"
        result = db.session.execute(text(query + limit))
        rows = result.fetchall()
        column_names = result.keys()  # Get the column names
        data = [dict(zip(column_names, row)) for row in rows]
        return data

    ##PRODUCT CATEGORY
    def get_product_categories(self):
        record_list = self.db.session.execute(db.select(ProductCategory).order_by(ProductCategory.name)).scalars().all()
        return record_list

    def get_product_category(self, id):
        record = self.db.session.execute(
            db.select(ProductCategory).where(ProductCategory.id == id).order_by(ProductCategory.name)).scalar()
        return record

    def get_product_category_by(self, keyword):
        if keyword == "":
            record_list = self.db.session.execute(
                db.select(ProductCategory).order_by(ProductCategory.name)).scalars().all()

        else:
            record_list = (self.db.session.execute(
                db.select(ProductCategory).where(ProductCategory.name.like(keyword)).order_by(ProductCategory.name))
                      .scalars().all())
        return record_list

    def get_product_category_name(self, name):
        record = self.db.session.execute(
            db.select(ProductCategory).where(ProductCategory.name == name).order_by(ProductCategory.name)).scalar()
        return record

    def add_category(self, details):
        with self.app.app_context():
            new_categ = ProductCategory(
                name=details['name'],
                status='ACTIVE')
            self.db.session.add(new_categ)
            self.db.session.commit()

    def product_category_change_stat(self, category_id):
        category_update = self.get_product_category(category_id)
        if category_update.status == "ACTIVE":
            category_update.status = "DEACTIVATED"
        else:
            category_update.status = "ACTIVE"
        self.db.session.commit()

    def update_product_category(self, details, category_id):
        category_update = self.get_product_category(category_id)
        if 'name' in details:
            category_update.name = details['name']
        self.db.session.commit()

    ##USER
    def get_user_details(self, user_id):
        record = self.db.session.execute(db.select(User).where(User.id == user_id)).scalar()
        return record

    def get_user(self, **user_details):
        record = User.query.filter_by(**user_details).scalar()
        return record

    def get_users(self, **user_details):
        records = User.query.filter_by(**user_details).all()
        return records

    def get_users_by(self, keyword, **where_cond):
        if keyword != "":
            keyword = f"%{keyword}%"
            record_list = User.query.filter_by(**where_cond).where(
                or_(User.fname.like(keyword), User.mname.like(keyword), User.lname.like(keyword)
                    , User.email.like(keyword), User.contact_no.like(keyword), User.address.like(keyword))).order_by(
                User.lname.asc()).all()
        else:
            record_list = User.query.filter_by(**where_cond).order_by(User.lname.asc()).all()
        return record_list

    def add_user(self, details: User):
        with self.app.app_context():
            details.status = 'ACTIVE'
            self.db.session.add(details)
            self.db.session.commit()

    def user_change_stat(self, user_id):
        user_to_update = self.get_user_details(user_id)
        if user_to_update.status == "ACTIVE":
            user_to_update.status = "DEACTIVATED"
        else:
            user_to_update.status = "ACTIVE"
        self.db.session.commit()

    def update_user(self, user_id, details: User):
        user_to_update = self.get_user_details(user_id)
        if details.email:
            user_to_update.email = details.email
        if details.fname:
            user_to_update.fname = details.fname
        if details.mname:
            user_to_update.mname = details.mname
        if details.lname:
            user_to_update.lname = details.lname
        if details.contact_no:
            user_to_update.contact_no = details.contact_no
        if details.address:
            user_to_update.address = details.address
        if details.postal_code:
            user_to_update.postal_code = details.postal_code
        if details.country:
            user_to_update.country = details.country
        if details.password:
            user_to_update.password = details.password
        self.db.session.commit()

    ## USER GROUP
    def get_user_group(self):
        record = self.db.session.execute(db.select(UserGroup).order_by(UserGroup.name)).scalars().all()
        return record

    def add_user_group(self, details: UserGroup):
        with self.app.app_context():
            self.db.session.add(details)
            self.db.session.commit()

    ##USER ACCESS
    def get_user_access(self, **user_details):
        record = UserAccess.query.filter_by(**user_details).scalar()
        return record

    def add_user_access(self, details: UserAccess):
        with self.app.app_context():
            self.db.session.add(details)
            self.db.session.commit()

    ##DISCOUNT
    def add_discount(self, details: Discount):
        self.db.session.add(details)
        self.db.session.commit()

    def get_discount(self):
        record = self.db.session.execute(db.select(Discount).order_by(Discount.code)).scalar()
        return record

    def get_discounts(self):
        record = self.db.session.execute(db.select(Discount).order_by(Discount.code)).scalars().all()
        return record

    def get_discount_code(self, code):
        record = self.db.session.execute(
            db.select(Discount).where(Discount.code == code.upper(), Discount.status == 'ACTIVE').order_by(
                Discount.code)).scalar()
        return record

    ##ORDERS
    def add_order(self, header: OrderHeader, items):
        with self.app.app_context():
            self.db.session.add(header)
            self.db.session.commit()
            for item in items:
                item.order_header_id = header.id
                self.db.session.add(item)
                self.db.session.commit()
            return header.id

    def update_to_cancel_order(self, id):
        order = self.get_order(id)
        order.status = 'CANCELLED'
        order.completion_date = func.now()
        self.db.session.commit()

    def update_to_paid_order(self, id, **stripe_session):
        order = self.get_order(id)
        order.status = 'PAID'
        order.paid_date = func.now()
        if stripe_session:
            order.stripe_session_id = stripe_session
        self.db.session.commit()

    def update_stripe_order(self, id, stripe_session):
        order = self.get_order(id)
        if stripe_session:
            order.stripe_session_id = stripe_session
            self.db.session.commit()

    def get_order(self, id):
        record = self.db.session.execute(
            db.select(OrderHeader).where(OrderHeader.id == id).order_by(OrderHeader.order_num)).scalar()
        return record

    def get_orders(self, keyword, **where_cond):
        if keyword != "":
            keyword = f"%{keyword}%"
            record_list = OrderHeader.query.filter_by(**where_cond).where(
                or_(OrderHeader.order_num.like(keyword), OrderHeader.status.like(keyword))).order_by(
                OrderHeader.order_date.asc()).all()
        else:
            record_list = OrderHeader.query.filter_by(**where_cond).order_by(OrderHeader.order_date.asc()).all()
        return record_list

    def get_orders_by(self, user_id):
        record = self.db.session.execute(
            db.select(OrderHeader).where(OrderHeader.user_id == user_id).order_by(
                OrderHeader.order_date)).scalars().all()
        return record

    def get_order_lines(self, order_header_id):
        record = self.db.session.execute(
            db.select(OrderLine).where(OrderHeader.id == order_header_id).order_by(
                OrderLine.order_header_id)).scalars().all()
        return record

    def count_orders_today(self):

        # Get the start and end of today
        today_start = datetime.combine(datetime.today(), datetime.min.time())
        today_end = datetime.combine(datetime.today(), datetime.max.time())

        # Query to count records created today
        count = db.session.query(func.count(OrderHeader.id)).filter(
            OrderHeader.order_date >= today_start,
            OrderHeader.order_date <= today_end
        ).scalar()  # Use .scalar() to get a single value

        return count

    def get_order_view(self, order_id):
        with self.app.app_context():
            order_query = """
                     SELECT order_header.order_num,order_header.order_date,order_header.order_by,
                     order_header.address, order_header.postal_code,order_header.country, 
                     order_header.discount_code, order_header.discount_total,order_header.discount_percent,
                     order_header.subtotal,order_header.total,
                     order_header.status as order_status, order_header.paid_date,order_header.completion_date, order_header.user_id,                  
                     order_line.*, product.img_path,
                     user.fname , user.mname, user.lname,user.contact_no
                     FROM order_header 
                     INNER JOIN order_line on order_header.id = order_line.order_header_id
                     INNER JOIN product on order_line.product_id = product.id
                     INNER JOIN user on order_header.user_id = user.id
                     """
            if order_id:
                order_query = order_query + " WHERE order_header.id =" + str(order_id)

            result = db.session.execute(text(order_query))
            rows = result.fetchall()
            column_names = result.keys()  # Get the column names
            data = [dict(zip(column_names, row)) for row in rows]

            return data

    ##CURRENCY
    def get_currency(self, currency_code):
        record = self.db.session.execute(
            db.select(ExchangeRate).where(ExchangeRate.currency_code == currency_code).order_by(
                ExchangeRate.currency_code)).scalar()
        return record

    def add_currency(self, new_currency: ExchangeRate):
        self.db.session.add(new_currency)
        self.db.session.commit()
