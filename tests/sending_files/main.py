#This is a test to make sure sending files to the server works as expected.

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
This function sends a request to the server to upload a file.
NOTE: You should check if the ID is unique before uploading the file, as done in generate_id, this is just a test to see if the file upload works.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to upload.
"""
def test_file_upload(username, auth_token, filename):
    print("NOTE: You should check if the ID is unique before uploading the file, as done in generate_id, this is just a test to see if the file upload works.")
    random_id = generate_random_string(10)
    data = {"userid": username, "auth_token": auth_token, "tempid": random_id}
    files = {"file": open(filename, "rb")}
    response = requests.post("http://localhost:5000/upload", data=data, files=files)
    print("Using random ID:", random_id)
    return response.json()

if __name__ == "__main__":
    username = "test"
    auth = "test"
    filename = "../shared_chunks/cat.png.hashes"
    print("Response: " + str(test_file_upload(username, auth, filename)))