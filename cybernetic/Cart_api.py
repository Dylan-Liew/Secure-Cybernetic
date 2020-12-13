from datetime import datetime
from flask_restx import Namespace, Resource
from flask import request, make_response, jsonify
from cybernetic import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from cybernetic.Models import CartItem, UserCart, Order, OrderedProduct, Address, Card
from cybernetic.schemas import UserCartSchema, CartItemSchema, OrderSchema, AddressSchema
from marshmallow import ValidationError
from cybernetic.AWS_Symmetric_Encryption_SDK import decrypt

api = Namespace("cart", description="Cart related")


@api.route("/")
class Cart(Resource):

    @jwt_required
    def get(self):
        user_id = get_jwt_identity()
        cart = UserCart.query.filter_by(id=user_id).first()
        items = cart.items
        total = 0
        for item in items:
            total += item.quantity * item.product.retail_price
        if cart is not None:
            cart_schema = UserCartSchema(
                exclude=["user", "items.product.id"])
            response_cart = cart_schema.dump(cart)
            response_cart["total_price"] = total
            response_obj = {
                "success": True,
                "data": response_cart
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "No such user cart"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def post(self):
        user_id = get_jwt_identity()
        cart = UserCart.query.filter_by(id=user_id).first()
        post_data = request.get_json(force=True)
        cart_item_schema = CartItemSchema(exclude=["product.id"])
        if cart is not None:
            cart_item = CartItem.query.filter_by(product_id=post_data.get("product_id"), cart_id=user_id).first()
            if cart_item is None:
                try:
                    post_data = cart_item_schema.load(post_data)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
                cart_item = CartItem(
                    cart_id=user_id,
                    product_id=post_data.get("product_id"),
                    quantity=post_data.get("quantity")
                )
                db.session.add(cart_item)
            else:
                cart_item.quantity += int(post_data.get("quantity"))
            db.session.commit()
            response_obj = {
                "success": True,
                "data": cart_item_schema.dump(cart_item)
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "No such user cart"
            }
            return make_response(jsonify(response_obj), 404)


@api.route("/checkout/")
class CartCheckout(Resource):

    @jwt_required
    def post(self):
        user_id = get_jwt_identity()
        cart = UserCart.query.filter_by(id=user_id).first()
        post_data = request.get_json(force=True)
        card = Card.query.filter_by(id=post_data.get("credit_card_id")).first()
        address = Address.query.filter_by(id=post_data.get("address_id")).first()
        if cart is not None and cart.items != []:
            if card:
                if cart.user_id == user_id and card.user_id == user_id:
                    if address:
                        if address.user_id == user_id:
                            items = cart.items
                            total = 0
                            for item in items:
                                total += item.quantity * item.product.retail_price
                            order = Order(
                                order_date=int(datetime.now().timestamp() * 1000),
                                total_price=total,
                                user_id=user_id,
                                address_id=post_data.get("address_id")
                            )
                            db.session.add(order)
                            db.session.commit()
                            for item in items:
                                ordered = OrderedProduct(
                                    order_id=order.id,
                                    product_id=item.product.id,
                                    quantity=item.quantity
                                )
                                db.session.delete(item)
                                db.session.add(ordered)
                            db.session.commit()
                            order_schema = OrderSchema(
                                exclude=["user", "items.product.id", "items.product.retail_price", "items.product.stock", "address_id"])
                            address = Address.query.filter_by(id=post_data.get("address_id")).first()
                            response_order = order_schema.dump(order)
                            address_schema = AddressSchema(exclude=["user"])
                            response_order["order_date"] = str(datetime.fromtimestamp(int(response_order["order_date"])/1000))
                            address = address_schema.dump(address)
                            address["address_2"] = decrypt(address["address_2"])
                            address["address_1"] = decrypt(address["address_1"])
                            address["contact"] = decrypt(address["contact"])
                            address["postal_code"] = decrypt(address["postal_code"])
                            address["contact"] = "*" * len(address["contact"][:-2]) + address["contact"][-2:]
                            response_order["address"] = address
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
                        address = Address.query.filter_by(user_id=user_id, default=True).first()
                        if address:
                            items = cart.items
                            total = 0
                            for item in items:
                                total += item.quantity * item.product.retail_price
                            order = Order(
                                order_date=int(datetime.now().timestamp() * 1000),
                                total_price=total,
                                user_id=user_id,
                                address_id=address.id
                            )
                            db.session.add(order)
                            db.session.commit()
                            for item in items:
                                ordered = OrderedProduct(
                                    order_id=order.id,
                                    product_id=item.product.id,
                                    quantity=item.quantity
                                )
                                db.session.delete(item)
                                db.session.add(ordered)
                            db.session.commit()
                            address_schema = AddressSchema(exclude=["user"])
                            order_schema = OrderSchema(
                                exclude=["user", "items.product.id", "items.product.retail_price", "items.product.stock", "address_id"])
                            response_order = order_schema.dump(order)
                            response_order["order_date"] = str(datetime.fromtimestamp(int(response_order["order_date"])/1000))
                            address = address_schema.dump(address)
                            address["address_2"] = decrypt(address["address_2"])
                            address["address_1"] = decrypt(address["address_1"])
                            address["contact"] = decrypt(address["contact"])
                            address["postal_code"] = decrypt(address["postal_code"])
                            address["contact"] = "*" * len(address["contact"][:-2]) + address["contact"][-2:]
                            response_order["address"] = address
                            response_obj = {
                                "success": True,
                                "data": response_order
                            }
                            return response_obj
                        else:
                            response_obj = {
                                "success": False,
                                "message": "No Address found"
                            }
                            return make_response(jsonify(response_obj), 404)
                else:
                    response_obj = {
                        "success": False,
                        "message": "Unauthorised Access"
                    }
                    return make_response(jsonify(response_obj), 403)
            else:
                response_obj = {
                    "success": False,
                    "message": "Card not found or No Card selected"
                }
                return make_response(jsonify(response_obj), 404)
        else:
            response_obj = {
                "success": False,
                "message": "No such user cart or No item in cart"
            }
            return make_response(jsonify(response_obj), 404)


@api.route("/items/<int:id>")
@api.param("id", "Cart Item identifier")
class CartItems(Resource):

    @jwt_required
    def put(self, id):
        user_id = get_jwt_identity()
        post_data = request.get_json(force=True)
        cart_item = CartItem.query.filter_by(id=id, cart_id=user_id).first()
        cart_item_schema = CartItemSchema(instance=cart_item, partial=True,
                                          exclude=["product.id"])
        if cart_item is not None:
            if cart_item.cart_id == user_id:
                try:
                    post_data = cart_item_schema.load(post_data)
                except ValidationError as err:
                    return {"errors": err.messages}, 422
                for key in post_data:
                    setattr(cart_item, key.lower(), post_data.get(key.lower()))
                db.session.commit()
                response_obj = {
                    "success": True,
                    "data": cart_item_schema.dump(cart_item)
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
                "message": "Cart item not found"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def delete(self, id):
        user_id = get_jwt_identity()
        cart_item = CartItem.query.filter_by(id=id).first()
        if cart_item is not None:
            if cart_item.cart_id == user_id:
                db.session.delete(cart_item)
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
                "message": "Cart Item not found"
            }
            return make_response(jsonify(response_obj), 404)
