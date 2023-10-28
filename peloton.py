from typing import Any, Dict, Text
import os
import requests
import json
from collections import defaultdict
import datetime
from dotenv import load_dotenv
load_dotenv()



PELOTON_API_ROOT = "https://api.onepeloton.com"


class PelotonAPI:

    def __init__(self):

        self.sess = requests.Session()

    def authenticate(self) -> requests.Response:
        """Authenticates the user with the Peloton API and creates a new session.

        The user_id in the response is needed to make other API calls.
        """
        payload = {
            "username_or_email": os.environ["PELOTON_USER"],
            "password": os.environ["PELOTON_PASS"]
        }

        response = self.sess.post(
            f"{PELOTON_API_ROOT}/auth/login",
            data=json.dumps(payload)
        )

        return response

    def get_recent_classes(self, fitness_discipline) -> Dict[Text, Any]:
        """Retrieves recent classes from the Peloton platform that are of the specified fitness discipline."""
        params = {
            "browse_category": fitness_discipline,
            "limit": 50,
            "sort_by": "original_air_time",
            "desc": True
        }

        response = self.sess.get(f"{PELOTON_API_ROOT}/api/v2/ride/archived",
                                 params=params)

        today = datetime.datetime.today().date()
        recent_classes = {}
        for w in response.json()['data']:
            workout_date = datetime.datetime.fromtimestamp(w['original_air_time']).date()

            if (today - workout_date).days > 7:
                break
            
            recent_classes[w['id']] = w

        return recent_classes

    def get_user_workouts(self, user_id, page: int = 0) -> Dict[Text, Any]:
        """Get the latest workouts for the user."""
        params = {
            "page": page,
            "limit": 50,
            "joins": "peloton.ride",
            "sort_by": "-created"
        }

        response = self.sess.get(
            f"{PELOTON_API_ROOT}/api/user/{user_id}/workouts",
            params=params
        )

        # Iterate through workouts and generate a list of workouts for the user.
        today = datetime.datetime.today().date()
        recent_workouts = defaultdict(list)
        for w in response.json()['data']:
            workout_date = datetime.datetime.fromtimestamp(w['created_at']).date()

            # Only get workouts from the last 7 days.
            if (today - workout_date).days > 7:
                break

            if 'ride' in w:
                title = w['ride']['title']
            elif 'peloton' in w:
                title = w['peloton']['ride']['title']
            else:
                title = "Unknown"
                
            lbl = f"{workout_date}: {title}"

            recent_workouts[str(workout_date)].append(lbl)

        return recent_workouts

    def favorite(self, id) -> requests.Response:
        """Favorites a class in the Peloton account for the user."""
        payload = {
            "ride_id": id
        }
        response = self.sess.post(f"{PELOTON_API_ROOT}/api/favorites/create",
                                  data=json.dumps(payload))

        return response

    def categories(self) -> Dict[Text, Any]:
        """Gets a list of Peloton fitness disciplines."""
        response = self.sess.get(f"{PELOTON_API_ROOT}/api/browse_categories?library_type=on_demand")
        return response.json()
