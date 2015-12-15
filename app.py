from flask import Flask, request, render_template
from uber_rides.auth import AuthorizationCodeGrant
from uber_rides.client import UberRidesClient
import json

CLIENT_ID = "TmORsdHDdk3GgGx3bBCE_Jh5EzaDbPKc"
CLIENT_SECRET = "dsPSgtSom4xyqgu8QcP-RPZ_DDju-pP-OKQdtMtW"
PERMISSION_SCOPES = {"profile", "history"}
REDIRECT_URL = "http://localhost:5000/loggedIn"

auth_flow = AuthorizationCodeGrant(CLIENT_ID,
				   PERMISSION_SCOPES,
				   CLIENT_SECRET,
				   REDIRECT_URL)

auth_url = auth_flow.get_authorization_url()


app = Flask(__name__)

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

	times_ran = 1

	for i in range (ride_count/50) :
		user_activity = client.get_user_activity(limit=50, offset=times_ran*50)
		result = user_activity.json
		complete_history.extend(result['history'])
		times_ran += 1

	cities = set()
	for i in complete_history:
		cities.add(i['start_city']['display_name'])

	return render_template('results.html',
						   ride_count=ride_count,
						   cities_count=len(cities))



if __name__ == "__main__":
	app.run(debug=True)

