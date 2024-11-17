import argparse
import requests
import random
import string
import os
import shutil
import hashlib
import math
import sys
import threading
import queue
from tqdm import tqdm
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
@param progress_bar: The progress bar to update.
@param CHECK_CHUNK_HASHES: Whether to check the hash of each chunk.
@param retries: The number of retries to attempt.
"""
class UploadFailedException(Exception):
    pass

progress_bar_lock = threading.Lock()  # Create a lock for the progress bar

def upload_file(username, auth_token, filename, unique_id, progress_bar, CHECK_CHUNK_HASHES, retries, exception_queue):
    chunk_hash = "IGNORE"
    if CHECK_CHUNK_HASHES:
        with open(filename, "rb") as f:
            chunk_data = f.read()
        chunk_hash = hashlib.sha256(chunk_data).hexdigest()
    
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id, "chunk_hash": chunk_hash}
    files = {"file": open(filename, "rb")}
    
    for attempt in range(retries):
        try:
            response = requests.post("{}/upload".format(SERVER_URL), data=data, files=files)
            response.raise_for_status()  # Raise an error for bad status codes
            response_data = response.json()
            if "error" in response_data:
                if DEBUG:
                    print(f"Server error: {response_data['error']}")
                raise requests.RequestException(response_data["error"])
            with progress_bar_lock:
                progress_bar.update(1)
            return response_data
        except Exception as e:
            if attempt < retries - 1:
                if DEBUG:
                    print(f"Upload failed (attempt {attempt + 1}/{retries}). Retrying... Error: {e}")
            else:
                if DEBUG:
                    print(f"Upload failed after {retries} attempts. Error: {e}")
                exception_queue.put(UploadFailedException(f"Failed to upload {filename} after {retries} attempts. Pass the --debug flag for more information."))
                return
        finally:
            files["file"].close()

"""
This function will remove the temp file client and server side in the event of an error.
@param unique_id: The unique ID to delete.
@username: The username of the user.
@auth_token: The authentication token of the user.
"""
def cleanup_failed_upload(unique_id, username, auth_token):
    if os.path.exists(unique_id):
        shutil.rmtree(unique_id)
        if DEBUG:
            print(f"Removed temp folder {unique_id}.")
    else:
        if DEBUG:
            print(f"Temp folder {unique_id} does not exist.")
    data = {"userid": username, "auth_token": auth_token, "tempid": unique_id}
    response = requests.post("{}/cleanup".format(SERVER_URL), data=data)
    if DEBUG:
        print(response.json())

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
    parser = argparse.ArgumentParser(description="Upload a file to the server.")
    parser.add_argument("filename", help="The name of the file to upload.")
    parser.add_argument("--username", help="The username of the user.")
    parser.add_argument("--auth_token", help="The authentication token of the user.")
    parser.add_argument("--server_url", help="The server URL.")
    parser.add_argument("--chunk_size", type=int, default=5, help="The size of each chunk in MB.")
    parser.add_argument("--check_hashes", action="store_true", help="Check the hash of the file.")
    parser.add_argument("--check_chunk_hashes", action="store_true", help="Check the hash of each chunk.")
    parser.add_argument("--rm", action="store_true", help="Remove the file after upload.")
    parser.add_argument("--retries", type=int, default=3, help="The number of retries for each chunk.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    USERNAME = args.username or os.getenv('C_DOWNLOADER_USERNAME')
    AUTH_TOKEN = args.auth_token or os.getenv('C_DOWNLOADER_AUTH_TOKEN')
    FILENAME = args.filename
    SERVER_URL = args.server_url or "http://localhost:5000"
    CHUNK_SIZE = args.chunk_size
    CHECK_HASHES = args.check_hashes
    CHECK_CHUNK_HASHES = args.check_chunk_hashes
    REMOVE_AFTER_UPLOAD = args.rm
    RETRIES = args.retries
    DEBUG = args.debug

    if not USERNAME or not AUTH_TOKEN:
        print("Username and auth token must be provided either as arguments or environment variables. Please set ENV variables C_DOWNLOADER_USERNAME and C_DOWNLOADER_AUTH_TOKEN.")
        sys.exit(1)

    # Prepare the file for upload
    unique_id = prepare_upload(FILENAME)
    if not unique_id:
        print(f"Cannot find file {FILENAME}.")
        sys.exit(1)

    print(f"Uploading file {FILENAME}.")

    # Deconstruct the file into chunks
    deconstruct_file(FILENAME, CHUNK_SIZE, unique_id, CHECK_HASHES, CHECK_CHUNK_HASHES)  # Use hash and chunk hashes

    # Get the list of chunks
    chunks = os.listdir(unique_id)
    total_chunks = len(chunks)

    # Track threads in a list
    threads = []
    exception_queue = queue.Queue()

    # Create a progress bar
    with tqdm(total=total_chunks, desc="Uploading chunks", unit="chunks") as progress_bar:
        # Upload the file to the server
        for chunk in chunks:
            thread = threading.Thread(target=upload_file, args=(USERNAME, AUTH_TOKEN, f"{unique_id}/{chunk}", unique_id, progress_bar, CHECK_CHUNK_HASHES, RETRIES, exception_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to finish
        for thread in threads:
            thread.join()  # Join only the threads you started, otherwise the program will hang

    # Check for exceptions
    while not exception_queue.empty():
        exception = exception_queue.get()
        print(f"Upload failed: {exception}")
        cleanup_failed_upload(unique_id, USERNAME, AUTH_TOKEN)
        sys.exit(1)

    # Cleanup the temp folder
    cleanup_upload(unique_id)

    print(f"Saved on the server as {FILENAME}.")

    if REMOVE_AFTER_UPLOAD:
        os.remove(FILENAME)
        print(f"Removed file {FILENAME}.")

    # Process the file on the server side
    validation = process_file_server_side(USERNAME, AUTH_TOKEN, unique_id, FILENAME)
    if(validation.get("error")):
        print(f"Error validating file: {validation.get('error')}")
    else:
        if DEBUG:
            print(f"File validated: {validation.get('success')}")