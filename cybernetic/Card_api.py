import random
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource
from flask import request, make_response, jsonify
from cybernetic import db
from cybernetic.Models import Card
from cybernetic.schemas import CardSchema
from marshmallow import ValidationError
from cybernetic.AWS_Symmetric_Encryption_SDK import encrypt, decrypt

api = Namespace("cards", description="Cards related")


@api.route("/")
class Cards(Resource):

    @jwt_required
    def get(self):
        user_identifier = get_jwt_identity()
        cards = Card.query.filter_by(user_id=user_identifier).all()
        cards_schema = CardSchema(many=True, exclude=["user", "expiry", "cvc"])
        response_cards = cards_schema.dump(cards)
        for card in response_cards:
            card["number"] = decrypt(card["number"])
            card["number"] = "*"*len(card["number"][:-4])+card["number"][-4:]
        response_obj = {
            "success": True,
            "data": {
                "cards": response_cards
            }
        }
        return response_obj

    @jwt_required
    def post(self):
        user_identifier = get_jwt_identity()
        post_data = request.get_json(force=True)
        card = Card.query.filter_by(number=decrypt(post_data.get("number"))).first()
        card_schema = CardSchema()
        try:
            card_schema.load(post_data)
        except ValidationError as err:
            return {"errors": err.messages}, 422
        if card is None:
            c_type = ""
            c_d = ["Credit", "Debit"]
            c_number = post_data.get("number")
            if c_number[0] == "4":
                c_type += "Visa "
            elif c_number[0] == "3":
                c_type += "AMEX "
            elif c_number[0] == "6":
                c_type += "Discover "
            else:
                c_type += "Mastercard "
            c_type += random.choice(c_d)
            c = Card(name=post_data.get("name"),
                     type=c_type,
                     cvc=encrypt(post_data.get("cvc")),
                     expiry=encrypt(post_data.get("expiry_year") + "/" + post_data.get("expiry_month")),
                     number=encrypt(c_number), user_id=user_identifier)
            db.session.add(c)
            db.session.commit()
            response_obj = {
                "success": True
            }
            return response_obj
        else:
            response_obj = {
                "success": False,
                "message": "Card already exist"
            }
            return make_response(jsonify(response_obj), 400)


@api.route("/<int:id>/")
@api.param("id", "Card identifier")
class CardDetails(Resource):

    @jwt_required
    def get(self, id):
        user_identifier = get_jwt_identity()
        card = Card.query.filter_by(id=id).first()
        if card is not None:
            if card.user_id == user_identifier:
                card_schema = CardSchema(exclude=["expiry", "cvc","user"])
                response_card = card_schema.dump(card)
                response_card["number"] = decrypt(response_card["number"])
                response_card["number"] = "*"*len(response_card["number"][:-4])+response_card["number"][-4:]
                response_obj = {
                    "success": True,
                    "data": response_card
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
                "message": "No such card"
            }
            return make_response(jsonify(response_obj), 404)

    @jwt_required
    def delete(self, id):
        user_identifier = get_jwt_identity()
        card = Card.query.filter_by(id=id).first()
        if card is not None:
            if card.user_id == user_identifier:
                db.session.delete(card)
                db.session.commit()
                response_obj = {
                    "success": True,
                }
                return make_response(jsonify(response_obj), 200)
            else:
                response_obj = {
                    "success": False,
                    "message": "Unauthorised Access"
                }
                return make_response(jsonify(response_obj), 403)
        else:
            response_obj = {
                "success": False,
                "message": "No such card"
            }
            return make_response(jsonify(response_obj), 404)
