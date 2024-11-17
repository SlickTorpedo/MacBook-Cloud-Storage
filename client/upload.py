#This is the client code that will upload a file to the server.

import requests
import random
import string
import os
import shutil
import hashlib
import math
import sys
import threading
from tqdm import tqdm

USERNAME = "test"
AUTH_TOKEN = "test"
SERVER_URL = "http://localhost:5000"
DEBUG = False

"""
This function generates a random string of a given length.
@param length: The length of the string to generate.
"""
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

"""
This function will check for a unique ID before uploading the file.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param unique_id: The unique ID to check.
"""
def check_unique_id(username, auth_token, unique_id):
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id}
    response = requests.post("{}/id".format(SERVER_URL), data=data)
    return response.json()

"""
This function sends a request to the server to upload a file.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param filename: The name of the file to upload.
@param unique_id: The unique ID to use for the upload.
"""
progress_bar_lock = threading.Lock()  # Create a lock for the progress bar
def upload_file(username, auth_token, filename, unique_id, progress_bar):
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id}
    files = {"file": open(filename, "rb")}
    response = requests.post("{}/upload".format(SERVER_URL), data=data, files=files)
    with progress_bar_lock:
        progress_bar.update(1)
    # return response.json()

"""This function will check if the file exists,
and give you a unique ID you can use for the folder chunking.
@param filename: The name of the file to upload.
"""
def prepare_upload(filename):
    if not os.path.exists(filename):
        return False
    unique_id = generate_random_string(10)
    if DEBUG:
        print("Checking if ID is unique...")
    while check_unique_id(USERNAME, AUTH_TOKEN, unique_id).get("error") or os.path.exists(unique_id):
        unique_id = generate_random_string(10)
        if DEBUG:
            print("ID is not unique, generating new ID...")
    if DEBUG:
        print("ID is unique. Using ID:", unique_id)
    return unique_id

"""This function will remove the temp folder after the file has been uploaded.
@param unique_id: The unique ID to delete.
"""
def cleanup_upload(unique_id):
    if os.path.exists(unique_id):
        shutil.rmtree(unique_id)
        if DEBUG:
            print(f"Removed temp folder {unique_id}.")
    else:
        if DEBUG:
            print(f"Temp folder {unique_id} does not exist.")

"""This function will send a request to the server to start processing and reassembling the file.
@param username: The username of the user.
@param auth_token: The authentication token of the user.
@param unique_id: The unique ID to process.
@param output_file: The name you want to save the file as (server side).
@param check_hash: Whether to check the hash of the file.
@param check_chunk_hashes: Whether to check the hash of each chunk.
"""
def process_file_server_side(username, auth_token, unique_id, output_file, check_hash=True, check_chunk_hashes=False):
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id, "output_file": output_file, "check_hash": check_hash, "check_chunk_hashes": check_chunk_hashes}
    response = requests.post("{}/process".format(SERVER_URL), data=data)
    if DEBUG:
        print(response.json())
    return response.json()

"""
This function deconstructs a file into chunks and stores them in a folder.
@param filename: The name of the file to deconstruct.
@param chunk_size: The size of each chunk in MB.
@param chunk_output: The folder to store the chunks.
@param use_hash: Whether to hash the file.
@param use_chunk_hashes: Whether to hash each chunk.
"""
def deconstruct_file(filename, chunk_size, chunk_output, use_hash, use_chunk_hashes):
    # Check if the file exists
    if not os.path.exists(filename):
        print(f"File {filename} does not exist.")
        sys.exit(1)

    # Check if the chunk output folder exists
    if not os.path.exists(chunk_output):
        os.mkdir(chunk_output)

    # Initialize hash objects
    file_hash_obj = hashlib.sha256()
    chunk_hashes = []

    # Open the file
    with open(filename, "rb") as f:
        data = f.read()
        file_size = os.path.getsize(filename)
        file_hash_obj.update(data)

    if use_hash:
        # Write the hash to a .hash file
        file_hash = file_hash_obj.hexdigest()
        with open(f"{chunk_output}/{filename}.hash", "w") as hash_file:
            hash_file.write(file_hash)

    # Calculate the number of chunks
    num_chunks = math.ceil(file_size / (chunk_size * 1024 * 1024))

    # Split the file into chunks
    with open(filename, "rb") as f:
        for i in range(num_chunks):
            start = i * chunk_size * 1024 * 1024
            end = min(file_size, (i + 1) * chunk_size * 1024 * 1024)
            chunk_data = data[start:end]
            
            # Hash each chunk if enabled
            if use_chunk_hashes:
                chunk_hash_obj = hashlib.sha256()
                chunk_hash_obj.update(chunk_data)
                chunk_hashes.append(chunk_hash_obj.hexdigest())

            # Write the chunk to a file
            with open(f"{chunk_output}/{filename}.{i}", "wb") as chunk_file:
                chunk_file.write(chunk_data)

    # Write chunk hashes to a .hashes file
    if use_chunk_hashes:
        with open(f"{chunk_output}/{filename}.hashes", "w") as hashes_file:
            hashes_file.write("\n".join(chunk_hashes))

    if DEBUG:
        print(f"File {filename} has been split into {num_chunks} chunks.")
    if use_hash:
        if DEBUG:
            print(f"Hash of file: {file_hash}")
    if use_chunk_hashes:
        if DEBUG:
            print(f"Chunk hashes saved to {filename}.hashes.")


if __name__ == "__main__":
    filename = "cat.png"
    chunk_size = 5  # In MB (default)
    CHECK_HASHES = True
    CHECK_CHUNK_HASHES = True
    REMOVE_AFTER_UPLOAD = False

    # Prepare the file for upload
    unique_id = prepare_upload(filename)
    if not unique_id:
        print(f"Cannot find file {filename}.")
        sys.exit(1)

    print(f"Uploading file {filename}.")

    # Deconstruct the file into chunks
    deconstruct_file(filename, chunk_size, unique_id, CHECK_HASHES, CHECK_CHUNK_HASHES)  # Use hash and chunk hashes

    # Get the list of chunks
    chunks = os.listdir(unique_id)
    total_chunks = len(chunks)

    # Track threads in a list
    threads = []

    # Create a progress bar
    with tqdm(total=total_chunks, desc="Uploading chunks", unit="chunks") as progress_bar:
        # Upload the file to the server
        for chunk in chunks:
            thread = threading.Thread(target=upload_file, args=(USERNAME, AUTH_TOKEN, f"{unique_id}/{chunk}", unique_id, progress_bar))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to finish
        for thread in threads:
            thread.join()  # Join only the threads you started, otherwise the program will hang

    # Cleanup the temp folder
    cleanup_upload(unique_id)

    print(f"Saved on the server as {filename}.")

    if REMOVE_AFTER_UPLOAD:
        os.remove(filename)
        print(f"Removed file {filename}.")

    # Process the file on the server side
    process_file_server_side(USERNAME, AUTH_TOKEN, unique_id, filename, CHECK_HASHES, CHECK_CHUNK_HASHES)
    #This can be done later, but it's better to do it now to save time.