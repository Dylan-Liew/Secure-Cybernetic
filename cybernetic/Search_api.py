from flask_restx import Namespace, Resource
from cybernetic import db, pagination
from flask import request, abort
from flask_jwt_extended import jwt_optional, get_jwt_identity
from cybernetic.Models import Product, User
from cybernetic.schemas import ProductSchema, UserSchema

api = Namespace("search", description="Search")


@api.route("/<model>/")
class Search(Resource):

  @jwt_optional
  def get(self, model: str):
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    args_query = request.args
    if len(args_query) == 0:
      return abort(400)
    if model.lower() == "product":
      schema = ProductSchema(many=True)
      query = f"%{args_query['name']}%"
      results = pagination.paginate(Product.query.filter(Product.name.like(query)), schema)
    elif model.lower() == "user":
      if user.id is None:
        return abort(401)
      elif not user.admin:
        return abort(403)
      schema = UserSchema(many=True, only=("email", "username", "email_verified", "active"))
      query = f"%{args_query['username']}%"
      results = pagination.paginate(User.query.filter(User.username.like(query)), schema)
    else:
      return abort(404)
    response_obj = {
      "success": True,
      "data": {
        "results": results
      }
    }
    return response_obj


