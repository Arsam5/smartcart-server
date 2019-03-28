from flask import Flask, request, jsonify, json
from cassandra.cluster import Cluster
import requests
import sys

cluster = Cluster(['cassandra'])
session = cluster.connect()

app = Flask(__name__)

API_KEY = 'gvak92gbyp6qfk2tpdp5wv32'

basee_url = 'http://api.walmartlabs.com/v1/items/{itemid}?format=json&apiKey={API_KEY}'
base_url = 'http://api.openweathermap.org/data/2.5/weather?q={city}&units={units}&APPID={API_KEY}'

@app.route('/')
def hello():
	name = request.args.get('name', 'World')
	return ('<h1>Hello, {}!<h1>'.format(name))


@app.route('/weather/<string:city>', methods=['GET'])
def get_weather(city):
	data = session.execute("""SELECT * FROM weather.city WHERE name = '{}' ALLOW FILTERING""".format(city))

	weather_url = base_url.format(city = city, units = 'metric', API_KEY = API_KEY)

	resp = requests.get(weather_url)

	if resp.ok:
		# print(resp.json())

		print(data, file=sys.stderr)

		res = resp.json()
		weather = {
			'id': data.id,
			'city': city,
			'temperature': res['main']['temp'],
			'description': res['weather'][0]['description'],
			'icon' : res['weather'][0]['icon']
		}

		return jsonify(weather), resp.status_code
	else:
		return resp.reason

@app.route('/weather/<int:id>', methods=['GET'])
def get_weather_by_id(id):

	#data = [x for x in cities if x['id'] == id]
	rows = session.execute("""SELECT * FROM weather.city WHERE id=%(id)s""",{'id': id})
	data = None
	for row in rows:
		data = row
	print(data, file=sys.stderr)
	weather_url = base_url.format(city = data.original, units = 'metric', API_KEY = API_KEY)

	resp = requests.get(weather_url)

	if resp.ok:
		# print(resp.json())
		print(data)
		res = resp.json()
		weather = {
			'id': id,
			'city': data.name,
			'original': data.original,
			'temperature': res['main']['temp'],
			'description': res['weather'][0]['description'],
			'icon' : res['weather'][0]['icon']
		}
		print(weather)

		return jsonify(weather), resp.status_code
	else:
		return resp.reason

@app.route('/weather', methods=['GET'])
def get_weather_for_all():
	weather_data = []

	cities = session.execute("SELECT * FROM weather.city")

	print(cities)
	for city in cities:
		print(city)
		weather_url = base_url.format(city = city.original, units = 'metric', API_KEY = API_KEY)
		print('before call')
		resp = requests.get(weather_url).json()

		if resp['cod'] == '404':
			continue
		print('before weather')
		weather = {
			'id': city.id,
			'name': city.name,
			'original': city.original,
			'temperature': resp['main']['temp'],
			'description': resp['weather'][0]['description'],
			'icon' : resp['weather'][0]['icon']
		}
		print('after weather')

		weather_data.append(weather)


	return jsonify(weather_data), 200

#_________________________________________________________________________________________________________________________________________________________________
#my post request for signup call
@app.route('/signup', methods = ['GET', 'POST'])
def signup_user():
	print('inside post')
	resp = session.execute("INSERT INTO smartcart.user(name,email,password) VALUES(%s, %s, %s)", (request.args['name'], request.args['email'], request.args['password']))
	resp['allowed']
	return jsonify({'message': '1'}), 201

#get product from database
@app.route('/product/<int:id>', methods=['GET'])
def get_product_by_id(id):

	#data = [x for x in cities if x['id'] == id]
	rows = session.execute("""SELECT * FROM smartcart.product WHERE id=%(id)s""",{'id': id})
	data = None
	for row in rows:
		data = row
	print(data, file=sys.stderr)
	product_url = basee_url.format(itemid = data.itemid, API_KEY = API_KEY)

	resp = requests.get(product_url)

	if resp.ok:
		# print(resp.json())
		print(data)
		res = resp.json()
		item = {
			'itemid': itemid,
			'name': data.name,
			'price': data.price,
			'description': data.description
		}
		print(item)

		return jsonify(item), resp.status_code
	else:
		return resp.reason

#________________________________________________________________________________________________________________________________________________________________
@app.route('/weather', methods = ['POST'])
def create_city():

	print('inside post')

	if not request.form or not 'city' in request.form:
		return jsonify({'Error': 'The new record needs to have a city name'}), 400

	print('before weather call')
	weather_url = base_url.format(city = request.form['city'], units = 'metric', API_KEY = API_KEY)
	resp = requests.post(weather_url, data = {'city': request.form['city']} ).json()
	print('after weather call')
	count_rows = session.execute("SELECT COUNT(*) FROM weather.city")

	#last_id = cities[-1]['id'];
	for c in count_rows:
		last_id = c.count
	last_id += 1
	print(last_id, file=sys.stderr)
	resp = session.execute("INSERT INTO weather.city(id,name,original,temperature,description,icon) VALUES(%s, %s, %s, %s, %s, %s)", (last_id, request.form['city'], request.form['city'], resp['main']['temp'], resp['weather'][0]['description'],resp['weather'][0]['icon']))
	print(resp, file=sys.stderr)
	#cities.append({'id': last_id, 'name':request.form['city'], 'original':request.form['city']})
	print('done')

	return jsonify({'message': 'created new city with weather'}), 201

@app.route('/weather/<int:id>', methods = ['PUT'])
def update_city(id):

	print('inside put')

	if not request.form or not 'city' in request.form:
		return jsonify({'Error': 'Record does not exist'}), 404

	print('inside update')
	rows = session.execute("""UPDATE weather.city SET name=%(name)s WHERE id=%(id)s""", {'name': request.form['city'], 'id': id})

	print('after update')

	return jsonify({'message':'updated: /weather/{}'.format(id)}), 200


@app.route('/weather/<string:city>', methods = ['DELETE'])
def delete_city(city):
	if not city:
		return jsonify({'Error': 'The city name is needed to delete'}), 400

	session.execute("""DELETE FROM weather.city WHERE name='{}'""".format(city))

	return jsonify({'message': 'deleted: /weather/{}'.format(city)}), 200

@app.route('/weather/<int:id>', methods = ['DELETE'])
def delete_city_by_id(id):
	if not id:
		return jsonify({'Error': 'The id is needed to delete'}), 400
	print('before delete')
	resp = session.execute("""DELETE FROM weather.city WHERE id={}""".format(id))
	print(resp)
	print('after delete')

	return jsonify({'message': 'deleted: /weather/{}'.format(id)}), 200


@app.route('/pokemon/<name>')
def profile(name):
	rows = session.execute("""SELECT * FROM pokemon.stats WHERE name = '{}'""".format(name))
	for pokemon in rows:
		return('<h1>{} has {} attack!</h1>'.format(name, pokemon.attack))

	return('<h1>That Pokemon does not exist!</h1>')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)
