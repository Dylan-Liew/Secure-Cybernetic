from cybernetic import ma
from marshmallow import fields, ValidationError
from cybernetic.Models import Order, OrderedProduct, UserCart, CartItem, Product, Card, User, Address, \
    ProductRating
from luhn import *


# Validation
def validate_card_number(value):
    # Validate Card Number Using Luhn
    try:
        int(value)
        if len(value) != 16 or not verify(value):
            raise ValidationError("Invalid Credit Card Number")
    except ValueError:
        raise ValidationError("Invalid Credit Card Number")


def validate_cvc(value):
    # Validate CVC
    try:
        int(value)
        if len(value) not in (3, 4):
            raise ValidationError("Invalid CVC")
    except ValueError:
        raise ValidationError("Invalid CVC")


def validate_expiry_year(value):
    # Validate Expiry Year
    try:
        if len(value) != 4 or int(value) < 2000:
            raise ValidationError("Invalid Expiry Year")
    except ValueError:
        raise ValidationError("Invalid Expiry Year")


def validate_expiry_month(value):
    # Validate Expiry Month
    try:
        if len(value) != 2 or 1 >= int(value) >= 12:
            raise ValidationError("Invalid Expiry Month")
    except ValueError:
        raise ValidationError("Invalid Expiry Month")


def validate_contact(value):
    try:
        int(value)
    except ValueError:
        raise ValidationError("Invalid Contact")


def validate_address1(value):
    if len(value) > 255:
        raise ValidationError("Invalid Address")


def validate_address2(value):
    if len(value) > 150:
        raise ValidationError("Invalid Address")


def validate_postal_code(value):
    try:
        int(value)
        if len(value) != 6:
            raise ValidationError("Invalid Postal Code")
    except:
        raise ValidationError("Invalid Postal Code")


def validate_rating(value):
    if 0 > value or value > 5:
        raise ValidationError("Invalid Rating")


def validate_price(value):
    if value != round(value, 2):
        raise ValidationError("Invalid Price")


# Schemas
class UserSchema(ma.SQLAlchemyAutoSchema):
    addresses = ma.List(ma.Nested("AddressSchema", exclude=("user",)), dump_only=True)
    cards = ma.List(ma.Nested("CardSchema", exclude=("user",)), dump_only=True)
    cart = ma.Nested("UserCartSchema", exclude=("user",), dump_only=True)
    product_rating = ma.List(ma.Nested("ProductRatingSchema", exclude=("user", "product")), dump_only=True)
    admin = ma.auto_field(dump_only=True)
    active = ma.auto_field(dump_only=True)
    enabled_2fa = ma.auto_field()
    email_verified = ma.auto_field(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        model = User


class CardSchema(ma.SQLAlchemyAutoSchema):
    user = ma.Nested("UserSchema", exclude=("addresses", "cards", "password", "cart", "product_rating", "admin",
                                            "enabled_2fa", "email_verified", "email", "username", "active", "id"))
    number = fields.Str(required=True, validate=validate_card_number)
    cvc = fields.Str(required=True, validate=validate_cvc)
    expiry_year = fields.Str(required=True, validate=validate_expiry_year)
    expiry_month = fields.Str(required=True, validate=validate_expiry_month)

    class Meta:
        model = Card


class AddressSchema(ma.SQLAlchemyAutoSchema):
    user = ma.Nested("UserSchema", exclude=("addresses", "cards", "password", "cart", "product_rating", "admin",
                                            "enabled_2fa", "email_verified", "email", "username", "active", "id"))

    contact = fields.Str(validate=validate_contact)
    address_1 = fields.Str(validate=validate_address1)
    address_2 = fields.Str(validate=validate_address2)
    postal_code = fields.Str(validate=validate_postal_code)

    class Meta:
        model = Address


class ProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User


class UserCartSchema(ma.SQLAlchemyAutoSchema):
    user = ma.Nested("UserSchema", exclude=("addresses", "cards", "password", "cart", "product_rating", "admin",
                                            "enabled_2fa", "email_verified", "email", "username", "active", "id"))
    items = ma.List(ma.Nested("CartItemSchema"))

    class Meta:
        model = UserCart


class ProductSchema(ma.SQLAlchemyAutoSchema):
    retail_price = fields.Float(required=True, validate=validate_price)
    stock = fields.Integer(required=True)

    class Meta:
        model = Product


class ProductRatingSchema(ma.SQLAlchemyAutoSchema):
    user = ma.Nested("UserSchema", exclude=("addresses", "cards", "password", "cart", "product_rating", "admin",
                                            "enabled_2fa", "email_verified", "email", "id", "active"))
    rating = fields.Integer(required=True, validate=validate_rating)
    comments = fields.Str(required=True)

    class Meta:
        model = ProductRating
        exclude = ("product",)


class CartItemSchema(ma.SQLAlchemyAutoSchema):
    product = ma.Nested("ProductSchema", exclude=("description", "pic_filename"))
    product_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True)

    class Meta:
        model = CartItem


class OrderSchema(ma.SQLAlchemyAutoSchema):
    user = ma.Nested("UserSchema", exclude=("addresses", "cards", "password", "cart", "product_rating", "admin",
                                            "enabled_2fa", "email_verified", "email", "username", "active", "id"))
    items = ma.List(ma.Nested("OrderedProductSchema"), dump_only=True)
    total_price = ma.Float(dump_only=True)
    tracking_no = fields.Str()
    address_id = fields.Integer()
    credit_card_id = fields.Integer()

    class Meta:
        model = Order


class OrderedProductSchema(ma.SQLAlchemyAutoSchema):
    product = ma.Nested("ProductSchema", exclude=("description", "pic_filename"))

    class Meta:
        model = OrderedProduct
