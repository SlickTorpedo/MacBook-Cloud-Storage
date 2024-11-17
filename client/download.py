import requests
import os
import hashlib
import shutil
import argparse
from tqdm import tqdm
import random
import string
import sys
from dotenv import load_dotenv

load_dotenv()

DEBUG = False

"""
This function generates a random string of a given length.
@param length: The length of the string to generate.
"""
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

"""
This function downloads a file from the server.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to download.
@param unique_id: The unique ID of the download.
"""
def download_file(username, auth_token, filename, unique_id):
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id, "filename": filename}
    try:
        response = requests.post("{}/download".format(SERVER_URL), data=data, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            print("File does not exist.")
        else:
            print(f"HTTP error occurred: {http_err}")
        remove_temp_folder(unique_id)
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred: {err}")
        remove_temp_folder(unique_id)
        sys.exit(1)
    return response

"""
This function retrieves the hash of a file from the server.
@param userid: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to retrieve the hash for.
"""
def retrieve_file_hash(userid, auth_token, filename):
    data = {"userid": userid, "auth_token": auth_token, "filename": filename}
    response = requests.post("{}/get_hash".format(SERVER_URL), data=data)
    return response.json()["hash"]

"""
This function reassembles a file from its chunks.
@param filename: The name of the file to reassemble.
@param chunk_folder: The folder containing the file chunks.
@param use_hash: Whether to use the hash to verify the file integrity.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
"""
def reassemble_file(filename, chunk_folder, use_hash=False, username=None, auth_token=None):
    file_hash_obj = hashlib.sha256()
    chunks = os.listdir(chunk_folder)
    chunks.sort(key=lambda x: int(x.split('.')[-1]))

    with open(filename, "wb") as output_file:
        for chunk in chunks:
            chunk_path = os.path.join(chunk_folder, chunk)
            with open(chunk_path, "rb") as chunk_file:
                chunk_data = chunk_file.read()
                output_file.write(chunk_data)

    if use_hash:
        with open(f"{filename}", "rb") as f:
            data = f.read()
            file_hash_obj.update(data)
            actual_file_hash = file_hash_obj.hexdigest()

        expected_file_hash = retrieve_file_hash(username, auth_token, filename)

        if actual_file_hash != expected_file_hash:
            raise ValueError("File hash mismatch! Expected {}, got {}. Your file may be corrupted!".format(expected_file_hash, actual_file_hash))
        
    if DEBUG:
        print(f"File {filename} has been reassembled.")
        if use_hash and DEBUG:
            print(f"Hash of file: {actual_file_hash}")

"""This function will remove the temp folder in the case of an error.
@param unique_id: The unique ID of the download.
"""
def remove_temp_folder(unique_id):
    try:
        shutil.rmtree(unique_id)
        if DEBUG:
            print(f"Removed temp folder {unique_id}.")
    except Exception as e:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and reassemble a file from the server.")
    parser.add_argument("filename", help="The name of the file to download.")
    parser.add_argument("--username", help="The username of the user.")
    parser.add_argument("--auth_token", help="The authentication token of the user.")
    parser.add_argument("--server_url", help="The server URL.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    USERNAME = args.username or os.getenv('C_DOWNLOADER_USERNAME')
    AUTH_TOKEN = args.auth_token or os.getenv('C_DOWNLOADER_AUTH_TOKEN')
    FILENAME = args.filename 

    FILENAME = os.path.basename(FILENAME)

    SERVER_URL = args.server_url or "http://localhost:5000"
    DEBUG = args.debug

    if not USERNAME or not AUTH_TOKEN:
        print("Username and auth token must be provided either as arguments or environment variables. Please set ENV variables C_DOWNLOADER_USERNAME and C_DOWNLOADER_AUTH_TOKEN.")
        sys.exit(1)

    UNIQUE_ID = unique_id = generate_random_string(10)
    while os.path.exists(UNIQUE_ID):
        UNIQUE_ID = generate_random_string(10)
    
    if not os.path.exists(UNIQUE_ID):
        os.mkdir(UNIQUE_ID)

    print(f"Looking for file {FILENAME}")

    response = download_file(USERNAME, AUTH_TOKEN, FILENAME, UNIQUE_ID)

    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024 * 1024
    with tqdm(total=total_size, desc="Downloading chunks", unit="B", unit_scale=True) as progress_bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                chunk_filename = f"{UNIQUE_ID}/{FILENAME}.{progress_bar.n // chunk_size}"
                with open(chunk_filename, "wb") as chunk_file:
                    chunk_file.write(chunk)
                progress_bar.update(len(chunk))

    reassemble_file(FILENAME, UNIQUE_ID, use_hash=True, username=USERNAME, auth_token=AUTH_TOKEN)

    shutil.rmtree(UNIQUE_ID)
    if DEBUG:
        print(f"Removed temp folder {UNIQUE_ID}.")

    print(f"File {FILENAME} has been downloaded and reassembled.")