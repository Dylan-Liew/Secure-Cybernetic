from flask import request, make_response, jsonify, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required, get_raw_jwt
from flask_restx import Namespace, Resource
from flask_mail import Message
from cybernetic import db, pagination, bcrypt, mail, url_serializer
from cybernetic.Models import User
from cybernetic.schemas import UserSchema
from marshmallow import ValidationError
from cybernetic.blacklist_helper import revoke_tokens


api = Namespace("users", description="Orders related")


@api.route("/")
class Users(Resource):

    @jwt_required
    def get(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        if user.admin:
            users_schema = UserSchema(many=True, only=("email", "username", "email_verified", "active"))
            users = pagination.paginate(User.query.filter_by(admin=False), users_schema)
            response_obj = {
                "success": True,
                "data": {
                    "users": users
                }
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)


@api.route("/<int:id>/")
@api.param("id", "User identifier")
class UserDetails(Resource):
    @jwt_required
    def delete(self, id):
        user_identifier = get_jwt_identity()
        user_identity = User.query.filter_by(id=user_identifier).first()
        if user_identity.admin:
            user = User.query.filter_by(id=id, active=True).first()
            if user is not None:
                user.active = False
                db.session.commit()
                response_obj = {
                    "success": True,
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "No such User/User already deactivated."
                }
                return make_response(jsonify(response_obj), 404)
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)


@api.route("/me/")
class Me(Resource):

    @jwt_required
    def get(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        user_schema = UserSchema(
            exclude=["cart", "password", "active", "product_rating", "cards", "addresses", "admin", "failed_login_attempts_count"])
        response_user = user_schema.dump(user)
        index_at_sign = response_user["email"].find("@")
        response_user["email"] = response_user["email"][:2] + "*"*(index_at_sign-2) + response_user["email"][index_at_sign:]
        response_obj = {
            "success": True,
            "data": response_user
        }
        return response_obj

    @jwt_required
    def put(self):
        user_schema = UserSchema()
        post_data = request.get_json(force=True)
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        try:
            data = user_schema.load(post_data, instance=user, partial=True)
        except ValidationError as err:
            return {"errors": err.messages}, 422
        for key in post_data:
            if key.lower() == "password":
                password = post_data.get("password")
                user.password = bcrypt.generate_password_hash(password).decode("utf-8")
                revoke_tokens(user_identifier)
            else:
                setattr(user, key.lower(), post_data.get(key.lower()))
        if "email" in post_data:
            user.email_verified = False
            db.session.commit()
            email = post_data.get("email")
            token = url_serializer.dumps(email, salt="192168876303253213878675934144992262075")
            msg = Message("Cybernetic Email Confirmation", sender="admin@idiotservice.net",
                          recipients=[email])
            link = url_for('auth_register_confirm_email', token=token, _external=True)
            msg.body = 'Your link is {} \n The link will expire in 5 Minutes'.format(link)
            mail.send(msg)
            response_obj = {
                "success": True,
                "message": "Please verify your email, the email confirmation link has sent to your email."
            }
            return response_obj
        else:
            db.session.commit()
            response_obj = {
                "success": True
            }
            return response_obj

    @jwt_required
    def delete(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        user.active = False
        db.session.commit()
        response_obj = {
            "success": True,
        }
        return response_obj
