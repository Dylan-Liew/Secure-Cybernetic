from flask_restx import Namespace, Resource
from flask import request, make_response, jsonify
from cybernetic import db
from cybernetic.Models import Address
from flask_jwt_extended import get_jwt_identity, jwt_required
from cybernetic.schemas import AddressSchema
from marshmallow import ValidationError
from cybernetic.AWS_Symmetric_Encryption_SDK import decrypt, encrypt

api = Namespace("address", description="Addresses related")


@api.route("/")
class Addresses(Resource):

    @jwt_required
    def get(self):
        user_identifier = get_jwt_identity()
        addresses = Address.query.filter_by(user_id=user_identifier).all()
        addresses_schema = AddressSchema(many=True, exclude=["user"])
        response_addresses = addresses_schema.dump(addresses)
        for address in response_addresses:
            address["address_2"] = decrypt(address["address_2"])
            address["address_1"] = decrypt(address["address_1"])
            address["contact"] = decrypt(address["contact"])
            address["postal_code"] = decrypt(address["postal_code"])
            address["contact"] = "*" * len(address["contact"][:-2]) + address["contact"][-2:]
        response_obj = {
            "success": True,
            "data": {
                "addresses": response_addresses
            }
        }
        return response_obj

    @jwt_required
    def post(self):
        user_identifier = get_jwt_identity()
        addresses_schema = AddressSchema()
        post_data = request.get_json(force=True)
        try:
            post_data = addresses_schema.load(post_data)
        except ValidationError as e:
            return {"success": False, "error": str(e)}
        address = Address.query.filter_by(description=post_data.get("description"), user_id=user_identifier).first()
        if address is None:
            try:
                address_2 = post_data.get("address_2")
            except KeyError:
                address_2 = None
            temp = Address.query.filter_by(user_id=user_identifier).all()
            if not temp:
                default = True
            else:
                default = False
            a = Address(description=post_data.get("description"),
                        contact=encrypt(post_data.get("contact")),
                        name=post_data.get("name"),
                        address_1=encrypt(post_data.get("address_1")),
                        address_2=encrypt(address_2),
                        postal_code=encrypt(post_data.get("postal_code")), user_id=user_identifier, default=default)
            db.session.add(a)
            db.session.commit()
            response_obj = {
                "success": True
            }
            return response_obj

        else:
            response_obj = {
                "success": False,
                "message": "Address already exist"
            }
            return make_response(jsonify(response_obj), 400)


@api.route("/<int:id>/")
@api.param("id", "Address identifier")
class AddressDetails(Resource):

    @jwt_required
    def get(self, id):
        user_identifier = get_jwt_identity()
        address = Address.query.filter_by(id=id).first()
        if address is not None:
            if user_identifier == address.user_id:
                addresses_schema = AddressSchema(exclude=["user"])
                response_address = addresses_schema.dump(address)
                response_address["address_2"] = decrypt(response_address["address_2"])
                response_address["address_1"] = decrypt(response_address["address_1"])
                response_address["contact"] = decrypt(response_address["contact"])
                response_address["postal_code"] = decrypt(response_address["postal_code"])
                response_address["contact"] = "*" * len(response_address["contact"][:-2]) + response_address["contact"][-2:]
                response_obj = {
                    "success": True,
                    "data": response_address
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
                "message": "No such Address saved"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def put(self, id):
        user_identifier = get_jwt_identity()
        address = Address.query.filter_by(id=id).first()
        addresses_schema = AddressSchema(exclude=["user"])
        post_data = request.get_json(force=True)
        try:
            post_data = addresses_schema.load(post_data, instance=address, partial=True)
        except ValidationError as e:
            return {"success": False, "error": str(e)}
        if address is not None:
            if user_identifier == address.user_id:
                for key in post_data:
                    if key.lower() == "default":
                        if post_data.get(key.lower()):
                            addresses = Address.query.filter_by(user_id=user_identifier).all()
                            for i in addresses:
                                setattr(i, "default", False)
                            setattr(address, key.lower(), post_data.get(key.lower()))
                        else:
                            response_obj = {
                                "success": False,
                                "message": "Invalid Value"
                            }
                            return make_response(jsonify(response_obj), 422)
                    elif key.lower() == "address_1" or key.lower() == "address_2" or key.lower() == "postal_code" or key.lower() == "contact":
                        setattr(address, key.lower(), encrypt(post_data.get(key.lower())))
                    else:
                        setattr(address, key.lower(), post_data.get(key.lower()))
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
                "message": "No such Address saved"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def delete(self, id):
        user_identifier = get_jwt_identity()
        address = Address.query.filter_by(id=id).first()
        if address is not None:
            if user_identifier == address.user_id:
                db.session.delete(address)
                db.session.commit()
                response_obj = {
                    "success": True,
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
                "message": "No such Address saved"
            }
            return make_response(jsonify(response_obj), 404)
