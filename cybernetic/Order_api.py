from flask_restx import Namespace, Resource
from flask import make_response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from cybernetic.Models import Order, User, Address
from cybernetic.schemas import OrderSchema, AddressSchema
from cybernetic import db, pagination
from datetime import datetime
from marshmallow import ValidationError
from cybernetic.AWS_Symmetric_Encryption_SDK import decrypt

api = Namespace("orders", description="Order related")


@api.route("/")
class Orders(Resource):

    @jwt_required
    def get(self):
        user_identifier = get_jwt_identity()
        user = User.query.filter_by(id=user_identifier).first()
        if user.admin:
            orders = Order
        else:
            orders = Order.query.filter_by(user_id=user_identifier)
        order_schema = OrderSchema(many=True,
                                   exclude=["user", "items.product.id", "items.product.retail_price",
                                            "items.product.stock"])
        response_orders = pagination.paginate(orders, order_schema)
        for order in response_orders["data"]:
            order["order_date"] = str(datetime.fromtimestamp(int(order["order_date"]) / 1000))
        response_obj = {
            "success": True,
            "data": response_orders
        }
        return response_obj


@api.route("/<int:id>/")
@api.param("id", "Order identifier")
class OrderDetail(Resource):

    @jwt_required
    def get(self, id):
        user_identifier = get_jwt_identity()
        order = Order.query.filter_by(id=id).first()
        user = User.query.filter_by(id=user_identifier).first()
        if order is not None:
            if user_identifier == order.user_id or user.admin:
                order_schema = OrderSchema(
                    exclude=["user", "items.product.id", "items.product.retail_price", "items.product.stock"])
                response_order = order_schema.dump(order)
                address_schema = AddressSchema(exclude=["user","id"])
                address = Address.query.filter_by(id=response_order["address_id"]).first()
                address = address_schema.dump(address)
                address["address_2"] = decrypt(address["address_2"])
                address["address_1"] = decrypt(address["address_1"])
                address["contact"] = decrypt(address["contact"])
                address["postal_code"] = decrypt(address["postal_code"])
                address["contact"] = "*" * len(address["contact"][:-2]) + address["contact"][-2:]
                response_order["address"] = address
                response_order["order_date"] = str(datetime.fromtimestamp(int(response_order["order_date"]) / 1000))
                response_obj = {
                    "success": True,
                    "data": response_order
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "Unauthorised Access"
                }
                return make_response(jsonify(response_obj), 403)
        else:
            response_obj = {
                "success": False,
                "message": "No such Order"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def post(self, id):
        user_identifier = get_jwt_identity()
        order = Order.query.filter_by(id=id).first()
        if order is not None:
            if user_identifier == order.user_id:
                order.confirm_received = True
                db.session.commit()
                response_obj = {
                    "success": True
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "Unauthorised Access"
                }
                return make_response(jsonify(response_obj), 403)
        else:
            response_obj = {
                "success": False,
                "message": "No such Order"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def put(self, id):
        user_identifier = get_jwt_identity()
        order = Order.query.filter_by(id=id).first()
        user = User.query.filter_by(id=user_identifier).first()
        if order is not None:
            if user.admin:
                post_data = request.get_json()
                schema = OrderSchema(only=["tracking_no"])
                try:
                    post_data = schema.load(post_data)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
                order.tracking_no = post_data.get("tracking_no")
                db.session.commit()
                order.confirm_received = True
                response_obj = {
                    "success": True
                }
                return response_obj
            else:
                response_obj = {
                    "success": False,
                    "message": "Unauthorised Access"
                }
                return make_response(jsonify(response_obj), 403)
        else:
            response_obj = {
                "success": False,
                "message": "No such Order"
            }
            return make_response(jsonify(response_obj), 404)
