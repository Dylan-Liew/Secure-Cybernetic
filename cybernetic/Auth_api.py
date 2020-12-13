import datetime
from flask import request, make_response, jsonify, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, get_raw_jwt, jwt_required
from flask_mail import Message
from flask_restx import Namespace, Resource
from itsdangerous import SignatureExpired, BadSignature
from marshmallow import ValidationError
from cybernetic import db, mail, bcrypt, url_serializer, jwt, app
from cybernetic.Models import User, UserCart
from cybernetic.schemas import UserSchema
from cybernetic.Models import User2FA
from cybernetic.blacklist_helper import (
    add_token_to_database,
    revoke_token
)

api = Namespace("auth", description="Auth related")


@api.route("/login/")
class Login(Resource):

    def post(self):
        post_data = request.get_json()
        schema = UserSchema(only=("email", "password"))
        try:
            post_data = schema.load(post_data)
        except ValidationError as err:
            return {"errors": err.messages}, 422
        email = post_data.get("email")
        password = post_data.get("password")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password) and user.active:
            if user.email_verified and not user.enabled_2fa:
                auth_token = create_access_token(identity=user.id,
                                                 expires_delta=datetime.timedelta(days=1, seconds=0))
                add_token_to_database(auth_token, app.config['JWT_IDENTITY_CLAIM'])
                if auth_token:
                    response_obj = {
                        "success": True,
                        "message": "Successfully logged in.",
                        "auth_token": auth_token
                    }
                    return response_obj
            elif not user.email_verified:
                token = url_serializer.dumps(email, salt="192168876303253213878675934144992262075")
                msg = Message("Cybernetic Email Confirmation", sender="admin@idiotservice.net",
                              recipients=[email])
                link = url_for('auth_register_confirm_email', token=token, _external=True)
                msg.body = 'Your link is {} \n The link will expire in 5 Minutes'.format(link)
                mail.send(msg)
                response_obj = {
                    "success": False,
                    "message": "Your email address hasn't been verified, A new link has been sent to your email, "
                               "please check your inbox",
                }
                return response_obj, 403
            elif user.enabled_2fa:
                msg = Message("Cybernetic 2FA PIN", sender="admin@idiotservice.net",
                              recipients=[email])
                two_factor = User2FA(user.id)
                db.session.add(two_factor)
                db.session.commit()
                msg.body = f'Your 2FA PIN is {two_factor.pin} \n The PIN will expire in 5 minute'
                mail.send(msg)
                response_obj = {
                    "success": True,
                    "message": "2FA required, A 6 digit PIN has been sent to your registered email address",
                    "2fa_required": True
                }
                return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "Incorrect username or password",
            }
            return response_obj, 401


@api.route("/login/second-factor/")
class LoginSecondStep(Resource):

    def post(self):
        post_data = request.get_json()
        pin = post_data["pin"]
        user_2fa = User2FA.query.filter_by(pin=pin, used=False).first()
        if user_2fa:
            if user_2fa.is_expired():
                response_obj = {
                    "success": False,
                    "message": "Token expired",
                }
                return response_obj, 403
            else:
                user_2fa.used = True
                db.session.commit()
                auth_token = create_access_token(identity=user_2fa.user_id,
                                                 expires_delta=datetime.timedelta(days=1, seconds=0))
                if auth_token:
                    response_obj = {
                        "success": True,
                        "message": "Successfully logged in.",
                        "auth_token": auth_token
                    }
                    return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "Invalid token",
            }
            return response_obj, 403


@api.route("/logout/")
class Logout(Resource):

    @jwt_required
    def get(self):
        user_identity = get_jwt_identity()
        token_jti = get_raw_jwt()["jti"]
        revoke_token(token_jti, user_identity)
        return {"success": True}


@api.route("/register/")
class Register(Resource):

    def post(self):
        post_data = request.get_json()
        schema = UserSchema()
        try:
            data = schema.load(post_data)
        except ValidationError as err:
            return {"errors": err.messages}, 422
        email = data["email"]
        username = data["username"]
        email_exist = User.query.filter_by(email=email).first()
        user_exist = User.query.filter_by(username=username).first()
        if not user_exist and not email_exist:
            user = User(
                email=email,
                password= data["password"],
                username=username
            )
            db.session.add(user)
            db.session.commit()
            cart = UserCart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()
            token = url_serializer.dumps(email, salt="192168876303253213878675934144992262075")
            msg = Message("Cybernetic Email Confirmation", sender="admin@idiotservice.net",
                          recipients=[email])
            link = url_for('auth_register_confirm_email', token=token, _external=True)
            # link = f"http://{app.config['DOMAIN']}/auth/register/confirm-email/{token}"
            msg.body = 'Your link is {} \n The link will expire in 5 Minutes'.format(link)
            mail.send(msg)
            response_obj = {
                "success": True,
                "message": "Successfully registered, confirmation email sent.",
            }
            return make_response(jsonify(response_obj), 201)
        else:
            response_obj = {
                "success": False,
                "message": "User already exists. Please Log in.",
            }
            return make_response(jsonify(response_obj), 202)


@api.route("/register/confirm-email/<token>")
class RegisterConfirmEmail(Resource):

    def get(self, token):
        try:
            email = url_serializer.loads(token, salt="192168876303253213878675934144992262075", max_age=300)
        except SignatureExpired:
            response_obj = {
                "success": False,
                "message": "Link has expired",
            }
            return response_obj, 403
        except BadSignature:
            response_obj = {
                "success": False,
                "message": "Invalid Token",
            }
            return response_obj, 403
        user = User.query.filter_by(email=email).first()
        user.email_verified = True
        db.session.commit()
        response_obj = {
            "success": True,
            "message": "Email confirmed successfully",
        }
        return response_obj


@api.route("/forget-password/")
class ForgetPasswordRequest(Resource):

    def post(self):
        post_data = request.get_json(force=True)
        schema = UserSchema(exclude=("username", "password"))
        try:
            post_data = schema.load(post_data)
        except ValidationError as err:
            return {"errors": err.messages}, 422
        email = post_data.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = url_serializer.dumps(email, salt="192168876303253213878675934144992262075")
            msg = Message("Cybernetic Forget Password", sender="admin@idiotservice.net",
                          recipients=[email])
            link = url_for('auth_forget_password_request_new', token=token, _external=True)
            # link = f"http://{app.config['DOMAIN']}/auth/register/confirm-email/{token}"
            msg.body = 'Your link is {} \n The link will expire in 5 Minutes'.format(link)
            mail.send(msg)
            response_obj = {
                "success": True,
                "message": "A reset password link has been sent to your email, "
                           "please check your inbox",
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "No user found with the email address provided",
            }
            return make_response(jsonify(response_obj), 404)


@api.route("/forget-password/new-password/<token>")
class ForgetPasswordRequestNew(Resource):

    def get(self, token):
        try:
            email = url_serializer.loads(token, salt="192168876303253213878675934144992262075", max_age=300)
        except SignatureExpired:
            response_obj = {
                "success": False,
                "message": "Link has expired",
            }
            return response_obj, 403
        except BadSignature:
            response_obj = {
                "success": False,
                "message": "Invalid Token",
            }
            return response_obj, 403
        response_obj = {
            "success": True,
            "message": "Please enter your new password"
        }
        return response_obj

    def post(self, token):
        try:
            email = url_serializer.loads(token, salt="192168876303253213878675934144992262075", max_age=300)
        except SignatureExpired:
            response_obj = {
                "success": False,
                "message": "Link as expired",
            }
            return response_obj, 403
        except BadSignature:
            response_obj = {
                "success": False,
                "message": "Invalid Token"
            }
            return response_obj, 403
        post_data = request.get_json(force=True)
        user = User.query.filter_by(email=email).first()
        password = post_data.get("password")
        user.password = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.commit()
        response_obj = {
            "success": True,
            "message": "Your password has been reset."
        }
        return response_obj
