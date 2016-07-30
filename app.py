import base64
from flask import Flask, request, redirect, render_template
from uber_rides.auth import AuthorizationCodeGrant
from uber_rides.client import UberRidesClient
import json
from collections import defaultdict

CLIENT_ID = "<YOUR_CLIENT_ID"
CLIENT_SECRET = "<YOUR_CLIENT_SECRET>"
PERMISSION_SCOPES = {"profile", "history"}
REDIRECT_URL = "https://ridestats.surbhioberoi.com/loggedIn"

auth_flow = AuthorizationCodeGrant(CLIENT_ID,
				   PERMISSION_SCOPES,
				   CLIENT_SECRET,
				   REDIRECT_URL)

auth_url = auth_flow.get_authorization_url()


app = Flask(__name__)

float_format = lambda x: float("{0:.2f}".format(x))

@app.route("/")
def hello():
	return render_template('uberlogin.html', url=auth_url)


@app.route("/loggedIn")
def post_login():
	session = auth_flow.get_session(request.url)
	client = UberRidesClient(session)
	complete_history = []

	user_activity = client.get_user_activity(limit=50)
	result = user_activity.json
	ride_count = result['count']
	complete_history.extend(result['history'])

	client_data = client.get_user_profile().json
	first_name = client_data['first_name']
	last_name = client_data['last_name']
	promo_code = client_data['promo_code']

	times_ran = 1

	for i in range (ride_count/50) :
		user_activity = client.get_user_activity(limit=50, offset=times_ran*50)
		result = user_activity.json
		complete_history.extend(result['history'])
		times_ran += 1

	cities = set()
	product_types = defaultdict(int)
	total_distance = 0
	wait_time = 0
	trip_time = 0

	for i in complete_history:
		cities.add(i['start_city']['display_name'])
		product_types[i['product_id']] += 1
		total_distance += i['distance']
		wait_time += (i['start_time'] - i['request_time'])/(60.0*60.0)
		trip_time += (i['end_time'] - i['start_time'])/(60.0*60.0)

	products = {}

	for key in product_types:
		try:
			productinfo = client.get_product(key)
			products[key] = productinfo.json
		except:
			pass

	uber_products =  defaultdict(int)
	for key in product_types:
		try:
			uber_products[products[key]['display_name']] += product_types[key]
		except:
		 	pass

	data = [first_name, last_name, "PS",]
	for i in uber_products:
		data.append(i)
		data.append(uber_products[i])

	data.extend(["PE", ride_count, len(cities), total_distance, wait_time, trip_time])

	encoded_data = base64.b64encode("|".join(map(lambda x: str(x), data)))

	shareurl = "https://ridestats.surbhioberoi.com/result/" + encoded_data
	
	return redirect(shareurl)


@app.route("/result/<string:hashed>")
def shareurl(hashed):
	data = base64.b64decode(hashed).split('|')
	products_start = data.index("PS") + 1
	products_end = data.index("PE")
	uber_products = {}
	for i in range(products_start, products_end-1, 2):
		uber_products[data[i]] = data[i+1]

	return render_template('results.html',
						   ride_count=int(data[products_end+1]),
						   cities_count=int(data[products_end+2]),
						   firstname=data[0],
						   lastname=data[1],
						   products=uber_products,
						   total_distance=float_format(float(data[products_end+3])*1.60934),
						   waittime=float_format(float(data[products_end+4])),
						   trip_time=float_format(float(data[products_end+5])),
						   fblink="https://ridestats.surbhioberoi.com" + request.path)



if __name__ == "__main__":
	app.run(host='0.0.0.0', port=4000, debug=True)

