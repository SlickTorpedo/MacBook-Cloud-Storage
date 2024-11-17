import requests
import os
import hashlib
import shutil
from tqdm import tqdm

USERNAME = "test"
AUTH_TOKEN = "test"
SERVER_URL = "http://localhost:5000"
DEBUG = False

"""
This function downloads a file from the server.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to download.
@param unique_id: The unique ID of the file.
"""
def download_file(username, auth_token, filename, unique_id):
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id, "filename": filename}
    response = requests.post("{}/download".format(SERVER_URL), data=data, stream=True)
    response.raise_for_status()  # Raise an error for bad status codes
    return response

"""
This function retrieves the hash of a file from the server.
@param userid: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to retrieve the hash of.
"""
def retrieve_file_hash(userid, auth_token, filename):
    data = {"userid": userid, "auth_token": auth_token, "filename": filename}
    response = requests.post("{}/get_hash".format(SERVER_URL), data=data)
    return response.json()["hash"]


"""
This function reassembles the file from the chunks and verifies the hash of the file.
You do NOT need to pass username and auth_token if you are not using the hash verification.
@param filename: The name of the file to reassemble.
@param chunk_folder: The folder to temporarily store the chunks.
@param use_hash: A boolean indicating whether to verify the hash of the file.
@param username: The username of the user. (Only pass if use_hash is True)
@param auth_token: The authentication token of the user. (Only pass if use_hash is True)
"""
def reassemble_file(filename, chunk_folder, use_hash=False, username=None, auth_token=None):
    # Initialize hash objects
    file_hash_obj = hashlib.sha256()

    # Get the list of chunks
    chunks = os.listdir(chunk_folder)
    chunks.sort(key=lambda x: int(x.split('.')[-1]))  # Sort chunks by their index

    # Reassemble the file
    with open(filename, "wb") as output_file:
        for chunk in chunks:
            chunk_path = os.path.join(chunk_folder, chunk)
            with open(chunk_path, "rb") as chunk_file:
                chunk_data = chunk_file.read()
                output_file.write(chunk_data)

    # Verify file hash
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

if __name__ == "__main__":
    filename = "cat.png"
    unique_id = "unique_id_example"

    # Create a folder for the chunks
    if not os.path.exists(unique_id):
        os.mkdir(unique_id)

    print(f"Downloading file {filename}.")

    # Download the file from the server
    response = download_file(USERNAME, AUTH_TOKEN, filename, unique_id)

    # Save the chunks
    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024 * 1024  # 1 MB
    with tqdm(total=total_size, desc="Downloading chunks", unit="B", unit_scale=True) as progress_bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                chunk_filename = f"{unique_id}/{filename}.{progress_bar.n // chunk_size}"
                with open(chunk_filename, "wb") as chunk_file:
                    chunk_file.write(chunk)
                progress_bar.update(len(chunk))

    # Reassemble the file
    reassemble_file(filename, unique_id, use_hash=True, username=USERNAME, auth_token=AUTH_TOKEN)

    # Cleanup the temp folder
    shutil.rmtree(unique_id)
    if DEBUG:
        print(f"Removed temp folder {unique_id}.")

    print(f"File {filename} has been downloaded and reassembled.")