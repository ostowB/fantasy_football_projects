#helper functions!

import requests
import math

def get_user(user_id=None, username=None):
    if user_id is not None: 
        return requests.get(f"https://api.sleeper.app/v1/user/" + user_id).json()
    elif username is not None: 
        return requests.get(f"https://api.sleeper.app/v1/user/" + username).json()
    else: 
        raise ValueError("Must provide either user_id or username.")

def z_to_percentile(z):
    return 100 * (1 + math.erf(z / math.sqrt(2))) / 2