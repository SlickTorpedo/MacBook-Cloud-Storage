#This is a test to make sure generating an ID works as expected.

#This feature, doubles a "status" feature to make sure the server is available.

import requests
import random
import string

"""
This function generates a random string of a given length.
@param length: The length of the string to generate.
"""
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


"""
This function sends a request to the server to check if the ID is unique.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
"""
def test_id_generation(username, auth_token):
    random_id = generate_random_string(10)
    data = {"userid": username, "auth_token": auth_token, "tempid": random_id}
    response = requests.post("http://localhost:5000/id", data=data)
    print("Using random ID:", random_id)
    return response.json()

if __name__ == "__main__":
    username = "test"
    auth = "test"
    print("Response: " + str(test_id_generation(username, auth)))