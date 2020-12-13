import datetime
import random

from cybernetic import db
from cybernetic import bcrypt


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    enabled_2fa = db.Column(db.Boolean, nullable=False, default=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    addresses = db.relationship("Address", backref="user", lazy=True)
    cards = db.relationship("Card", backref="user", lazy=True)
    product_rating = db.relationship("ProductRating", backref="user", lazy=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    locked = db.Column(db.Boolean, nullable=False, default=False)
    orders = db.relationship("Order", backref="user", lazy=True)
    user2fa = db.relationship("User2FA", backref="user", lazy=True)
    login_attempts = db.relationship("LoginAttempts", backref="user", lazy=True)
    failed_login_attempts_count = db.Column(db.Integer, nullable=False, default=0)
    cart = db.relationship("UserCart", uselist=False, back_populates="user")

    def __init__(self, username, email, password, admin=False, email_verified=False):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.admin = admin
        self.email_verified = email_verified

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class User2FA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pin = db.Column(db.String(6), unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    expiry = db.Column(db.String(100), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, user_id):
        expired_dt = datetime.datetime.now() + datetime.timedelta(seconds=300)
        system_random = random.SystemRandom()
        self.user_id = user_id
        self.pin = str(system_random.randrange(100000, 999999))
        self.expiry = str(expired_dt.timestamp())

    def is_expired(self):
        expiry_time = float(self.expiry)
        now = datetime.datetime.now().timestamp()
        if now > expiry_time:
            return True
        else:
            return False

    def __repr__(self):
        return f"User2FA('{self.user_id}', '{self.pin}')"


class LoginAttempts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(20), nullable=False)
    successful = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.String(100), nullable=False)

    def __init__(self, ip_address, successful, user_id):
        self.ip_address = ip_address
        self.successful = successful
        self.user_id = user_id
        self.timestamp = datetime.datetime.now().timestamp()

    def __repr__(self):
        return f"LoginAttempt('{self.user_id}', '{self.successful}', '{self.ip_address}')"


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'token_id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_identity': self.user_identity,
            'revoked': self.revoked,
            'expires': self.expires
        }


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    contact = db.Column(db.String(1000), unique=False, nullable=False)
    description = db.Column(db.String(20), unique=False, nullable=False)
    address_1 = db.Column(db.String(1000), nullable=False)
    address_2 = db.Column(db.String(1000), nullable=True)
    postal_code = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    default = db.Column(db.Boolean, nullable=False, default=False)
    orders = db.relationship("Order", backref="address", lazy=True)

    def __repr__(self):
        return f"Address('{self.description}', '{self.address_1} {self.address_2} {self.postal_code}')"


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    name = db.Column(db.String(30), nullable=False)
    number = db.Column(db.String(1000), nullable=False)
    cvc = db.Column(db.String(1000), nullable=False)
    expiry = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Card('{self.name}', '{self.number}', '{self.cvc}', '{self.expiry}')"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    retail_price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text(500), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    pic_filename = db.Column(db.String(255), nullable=False)
    cart_item = db.relationship("CartItem", backref="product", lazy=True)
    product_rating = db.relationship("ProductRating", backref="product", lazy=True)
    ordered_product = db.relationship("OrderedProduct", backref="product", lazy=True)

    def __repr__(self):
        return f"Product('{self.name}', '{self.retail_price}', '{self.stock}')"


class UserCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", backref="cart", lazy=True)

    def __repr__(self):
        return f"UserCart('{self.id}','{self.user_id}')"


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("user_cart.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"CartItem('{self.id}', '{self.cart_id}','{self.product_id}','{self.quantity}')"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.DECIMAL, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    items = db.relationship("OrderedProduct", backref="order", lazy=True)
    tracking_no = db.Column(db.String(30), nullable=True, default=None)
    confirm_received = db.Column(db.Boolean, nullable=False, default=False)
    address_id = db.Column(db.Integer, db.ForeignKey("address.id", ondelete='SET NULL'), nullable=True)

    def __repr__(self):
        return f"Order('{self.id}', '{self.order_date}','{self.total_price}','{self.user_id}'')"


class OrderedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Ordered('{self.id}', '{self.order_id}','{self.product_id}','{self.quantity}')"


class ProductRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text(500), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"ProductRating('{self.id}','{self.rating}, {self.product_id}')"
