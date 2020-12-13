from flask import Flask
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from .Paginate import Pagination

app = Flask(__name__)
app.secret_key = "5791628bb0b13ce0c676dfde280ba245"
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]
app.config["MAIL_SERVER"] = "smtp.mailgun.org"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "postmaster@mail.idiotservice.net"
app.config["MAIL_PASSWORD"] = "b4da58f53eb2d3f639fe4b978f216bc7-ffefc4e4-d350ddca"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.url_map.strict_slashes = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

url_serializer = URLSafeTimedSerializer(app.secret_key)
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)
bcrypt = Bcrypt(app)


@app.after_request
def apply_secure_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route('/')
def cybernetic():
    return "<head><title>Cybernetic</title></head>"


app.config["PAGINATE_PAGE_SIZE"] = 10
app.config["PAGINATE_MAX_SIZE"] = 20
pagination = Pagination(app, db)

api = Api(app, version="1.0", title="Cybernetic", doc="", add_specs=False)

from cybernetic.User_api import api as users_api
from cybernetic.Auth_api import api as auth_api
from cybernetic.Card_api import api as cards_api
from cybernetic.Address_api import api as address_api
from cybernetic.Product_api import api as product_api
from cybernetic.Cart_api import api as cart_api
from cybernetic.Order_api import api as order_api
from cybernetic.Review_api import api as review_api
from cybernetic.Search_api import api as search_api
from .blacklist_helper import is_token_revoked

api.add_namespace(users_api)
api.add_namespace(auth_api)
api.add_namespace(cards_api)
api.add_namespace(address_api)
api.add_namespace(product_api)
api.add_namespace(cart_api)
api.add_namespace(order_api)
api.add_namespace(review_api)
api.add_namespace(search_api)


@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)
