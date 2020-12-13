import os
import uuid
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename
from cybernetic.Models import Product, User
from cybernetic import db, pagination
from flask import request, make_response, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from cybernetic.schemas import ProductSchema
from marshmallow import ValidationError

api = Namespace("products", description="Product related")
UPLOAD_FOLDER = "./cybernetic/uploads/"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gen_unique_filename(filename):
    unique = str(uuid.uuid4())
    name = filename.split(".")[0]
    name += unique
    return f"{name}.{filename.split('.')[1]}"


@api.route("/uploads/")
class ImageUpload(Resource):

    @jwt_required
    def post(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        if user.admin:
            if "file" not in request.files:
                response_obj = {
                    "success": False,
                    "message": "no file part"
                }
                return make_response(jsonify(response_obj), 400)
            file = request.files["file"]
            if file.filename == "":
                response_obj = {
                    "success": False,
                    "message": "no file part"
                }
                return make_response(jsonify(response_obj), 400)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = gen_unique_filename(filename)
                file.save(os.path.abspath(UPLOAD_FOLDER + filename))
                response_obj = {
                    "success": True,
                    "data": {
                        "filename": filename
                    }
                }
                return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)


@api.route("/uploads/<filename>")
class GetImage(Resource):

    def get(self, filename):
        return send_from_directory(os.path.abspath(UPLOAD_FOLDER), filename)


@api.route("/")
class Products(Resource):

    @jwt_optional
    def get(self):
        product_schema = ProductSchema(many=True)
        products = pagination.paginate(Product, product_schema)
        response_obj = {
            "success": True,
            "data": {
                "products": products
            }
        }
        return response_obj

    @jwt_required
    def post(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        post_data = request.get_json(force=True)
        product = Product.query.filter_by(name=post_data.get("name")).first()
        product_schema = ProductSchema()
        if user.admin:
            if not product:
                try:
                    post_data = product_schema.load(post_data)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
                product = Product(
                    name=post_data.get("name"),
                    retail_price=post_data.get("retail_price"),
                    description=post_data.get("description"),
                    stock=post_data.get("stock"),
                    pic_filename=post_data.get("pic_filename")
                )
                db.session.add(product)
                db.session.commit()
                product_schema = ProductSchema()
                response_obj = {
                    "success": True,
                    "data": product_schema.dump(product)
                }
                return make_response(jsonify(response_obj), 201)
            else:
                response_obj = {
                    "success": False,
                    'message': "Product already exists.",
                }
                return make_response(jsonify(response_obj), 202)
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)


@api.route("/<id>/")
@api.param("id", "Product identifier")
class ProductDetails(Resource):

    @jwt_optional
    def get(self, id):
        product = Product.query.filter_by(id=id).first()
        if product is not None:
            product_schema = ProductSchema()
            response_obj = {
                "success": True,
                "data": product_schema.dump(product)
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "No such Product"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def put(self, id):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        product = Product.query.filter_by(id=id).first()
        post_data = request.get_json(force=True)
        product_schema = ProductSchema()
        if user.admin:
            if product is not None:
                try:
                    post_data = product_schema.load(post_data)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
                for key in post_data:
                    setattr(product, key.lower(), post_data.get(key.lower()))
                db.session.commit()
                product_schema = ProductSchema()
                response_obj = {
                    "success": True,
                    "data": product_schema.dump(product)
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "No such Product"
                }
                return make_response(jsonify(response_obj), 404)
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)

    @jwt_required
    def delete(self, id):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        product = Product.query.filter_by(id=id).first()
        if user.admin:
            if product is not None:
                db.session.delete(product)
                db.session.commit()
                response_obj = {
                    "success": True,
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "No such Product"
                }
                return make_response(jsonify(response_obj), 404)
        else:
            response_obj = {
                "success": False,
                "message": "Unauthorised Access"
            }
            return make_response(jsonify(response_obj), 403)
