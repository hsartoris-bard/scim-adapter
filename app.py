from flask import Flask, request
from flask_restful import Resource, Api, fields, marshal_with, marshal, reqparse
import redis
import scimschema
import copy
import json

rd = redis.Redis(host='localhost', port=6379, db=1)
prefix = "User"

app = Flask(__name__)
api = Api(app)

known_users = ['901377171@bard.edu']

parser = reqparse.RequestParser()
parser.add_argument('id')
parser.add_argument('name', type=dict)

user_schema = {
		'schemas': 	fields.List(fields.String, default = [ "urn:ietf:params:scim:schemas:core:2.0:User" ]),
		'id':		fields.String(attribute = "eduPersonPrincipalName"),
		'userName': fields.String(attribute = 'eduPersonPrincipalName'),
		'meta': {
			'resourceType': fields.String(default = 'User'),
			'location': fields.FormattedString('/Users/{eduPersonPrincipalName}')
			}
		}

error_schema = {
		'status':  fields.Integer,
		'detail':  fields.String,
		'schemas': fields.List(fields.String, default = [ 'urn:ietf:params:scim:api:messages:2.0:Error' ]),
		}

internal_user_schema = {
		'eduPersonPrincipalName': fields.String(attribute = 'id'),
		'givenName': fields.String(attribute = 'name.givenName'),
		}

def get_user(user_id):
	cache_key = f'{prefix}:{user_id}'
	user = rd.get(cache_key)
	if user:
		return json.loads(user)

	if user_id in known_users:
		user = {"eduPersonPrincipalName": user_id}
		rd.set(cache_key, json.dumps(user))
		return user
	return None

@marshal_with(error_schema)
def get_error(status, detail = None):
	if detail:
		return {'status': status, 'detail': detail}
	else:
		return {'status': status}


class Users(Resource):
	def get(self, user_id = None):
		if user_id:
			user = get_user(user_id)
			if user:
				return marshal(user, user_schema)
			return get_error(404, f'Requested user {user_id} not found'), 404
		return get_error(404, 'No user requested'), 404

	def post(self):
		args = parser.parse_args()
		print(args)
		if not request.json:
			return Error(500), 500
		print(request.json)

	def put(self, user_id):
		args = parser.parse_args()
		userobj = marshal(args, internal_user_schema)
		rd.set(f'{prefix}:{user_id}', json.dumps(userobj))
		return marshal(userobj, user_schema), 201

api.add_resource(Users, '/Users', '/Users/<string:user_id>')

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8888, debug=True)
