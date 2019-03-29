from flask import Flask, request, jsonify, json
from cassandra.cluster import Cluster
import requests
import sys

cluster = Cluster(['cassandra'])
session = cluster.connect()

app = Flask(__name__)

API_KEY = 'gvak92gbyp6qfk2tpdp5wv32'

basee_url = 'http://api.walmartlabs.com/v1/items/{itemId}?format=json&apiKey={API_KEY}'
base_url = 'http://api.openweathermap.org/data/2.5/weather?q={city}&units={units}&APPID={API_KEY}'

@app.route('/')
def hello():
	name = request.args.get('name', 'World')
	return ('<h1>Hello, {}!<h1>'.format(name))

#_________________________________________________________________________________________________________________________________________________________________
#my post request for signup call
@app.route('/signup', methods = ['GET', 'POST'])
def signup_user():
	print('inside post')
	resp = session.execute("INSERT INTO smartcart.user(id,name,email,password) VALUES(%s, %s, %s, %s)", (int(request.args['id']),request.args['name'], request.args['email'], hash(request.args['password'])))
	return jsonify({'message': '1'}), 201

#login call
@app.route('/login',methods =['POST'])
def login_user():
	rows = session.execute("""select name from smartcart.user where email =%(email)s ALLOW FILTERING""",{'email': request.args['email']})
	data = None

	for row in rows:
		data = row
		print(row)

	if data:
		return jsonify({'message': '1'.format(id)}), 200
	else:
		return resp.reason

#get product from database
@app.route('/product/<int:itemId>', methods=['GET'])
def get_product_by_id(itemId):

	#data = [x for x in cities if x['id'] == id]
	#comment
	rows = session.execute("""SELECT * FROM smartcart.products WHERE itemId=%(itemId)s""",{'itemId': itemId})
	data = None

	for row in rows:
		data = row
		print(row)

	product_url = basee_url.format(itemId = itemId, API_KEY = API_KEY)

	resp = requests.get(product_url)

	if resp.ok:
		# print(resp.json())

		res = resp.json()
		item = {
			'itemId': itemId,
			'name': data.name,
			'price': res['salePrice'],
			'description': data.description
		}


		return jsonify(item), resp.status_code
	else:
		return resp.reason


#insert product into database
@app.route('/items', methods= ['POST'])
def create_product():

	print ('fuck off')

	product_url = basee_url.format(itemId = request.args['itemId'] , API_KEY= API_KEY)
	print(product_url)
	resp = request.post(product_url,data = {'itemId':request.args['itemId']}).json()
	print('after product call')



	count_rows = session.execute("SELECT COUNT(*) FROM smartcart.products")

	for c in count_rows:
		last_id = c.count
	last_id += 1

	print(request.form['name'])

	# print(request.args)
	resp = session.execute("INSERT INTO smartcart.product(itemId,description,id,name,price) VALUES(%s, %s, %s, %s, %s)", (request.form['itemId'], request.form['shortDescription'], last_id,request.form['name'], request.form['salePrice']))

	print('done')

	return jsonify({'message': 'added'}), 201

#delete product from database by itemid
@app.route('/deleteproduct/<int:itemId>', methods = ['DELETE'])
def delete_product_by_id(itemId):
	# if not itemId:
	# 	return jsonify({'Error': 'The id is needed to delete'}), 400
	print('before delete')
	resp = session.execute("""DELETE FROM smartcart.products WHERE itemId={}""".format(itemId))

	return jsonify({'message': 'deleted'.format(itemId)}), 200

#edit product into database
@app.route('/editproduct/<int:itemId>', methods = ['PUT'])
def update_product(itemId):

	print('inside put')

	#if not request.args or not 'itemId' in request.args:
	#	return jsonify({'Error': 'Record does not exist'}), 404

	print('inside update')
	rows = session.execute("""UPDATE smartcart.products SET name=%(name)s WHERE itemId=%(itemId)s""", {'name': request.args['name'], 'itemId': itemId})

	print('after update')

	return jsonify({'message':'1'.format(id)}), 200


#________________________________________________________________________________________________________________________________________________________________

@app.route('/pokemon/<name>')
def profile(name):
	rows = session.execute("""SELECT * FROM pokemon.stats WHERE name = '{}'""".format(name))
	for pokemon in rows:
		return('<h1>{} has {} attack!</h1>'.format(name, pokemon.attack))

	return('<h1>That Pokemon does not exist!</h1>')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)
