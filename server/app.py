# Flask app for accepting the files and returning the results.
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import hashlib
import shutil
import dotenv
import json

dotenv.load_dotenv()

print("Loading user system...")
#Look in the ENV for the "USERS" variable, which contains the users and their auth tokens.
USERS = os.getenv("USERS")
if not USERS:
    print("No users found in the ENV. Please create an ENV file and set the USERS variable to a JSON object with the users and their auth tokens.")
    sys.exit(1)

try:
    USERS = json.loads(USERS)
except Exception as e:
    print("Error parsing users JSON: " + str(e))
    sys.exit(1)

print("Users loaded.")



app = Flask(__name__)
CORS(app)

# This operates on a user system, so each user gets a folder with their files.
# The "uploads" folder contains all the files uploaded by all users.
UPLOAD_FOLDER = "uploads"

def authorize_user(userid, auth_token):
    if userid not in USERS:
        return False
    return USERS[userid] == auth_token

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "OK"})

# When a user uploads a file, it will contain a "tempid" field.
# This tempid is used as the folder name for the user while the file is being processed.
# Then, once the file is processed, the file is saved in the users folder with the proper filename, and the tempid folder is deleted.
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    tempid = request.form["tempid"]
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    chunk_hash = request.form["chunk_hash"]
    if chunk_hash == "IGNORE":
        chunk_hash = None
    
    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    # Create a folder for the user if it doesn't exist
    user_folder = f"{UPLOAD_FOLDER}/{userid}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    try:
        file.save(f"{temp_folder}/{file.filename}")
        if(chunk_hash):
            file_hash_obj = hashlib.sha256()
            with open(f"{temp_folder}/{file.filename}", "rb") as f:
                data = f.read()
                file_hash_obj.update(data)
                file_hash = file_hash_obj.hexdigest()
            if file_hash != chunk_hash:
                return jsonify({"error": "File hash mismatch!"})
        return jsonify({"success": "File uploaded"})
    except Exception as e:
        return jsonify({"error": "Error saving file: " + str(e)})


def check_file_exists(userid, filename):
    file_path = os.path.join(UPLOAD_FOLDER, userid, filename)
    return os.path.exists(file_path)

@app.route("/id", methods=["POST"])
def check_id():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]
    filename = request.form["filename"]
    
    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    # Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        if not check_file_exists(userid, filename):
            return jsonify({"success": "ID is unique"})
        else:
            return jsonify({"error": "File already exists"})
    else:
        return jsonify({"error": "ID already exists"})
    
@app.route("/process", methods=["POST"])
def process_file():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]
    output_file = request.form["output_file"]
    
    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    # Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        return jsonify({"error": "Temp folder does not exist"})
    
    # Get the list of files in the temp folder
    files = os.listdir(temp_folder)
    if len(files) == 0:
        return jsonify({"error": "No files in temp folder"})
    
    # Read the file-wide hash
    hash_value = None
    check_hash = os.path.exists(f"{temp_folder}/{output_file}.hash")
    if check_hash:
        hash_file = f"{temp_folder}/{output_file}.hash"
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                hash_value = f.read()
        else:
            return jsonify({"error": "Hash file does not exist"})
    
    # Read the chunk hashes
    chunk_hashes = []
    check_chunk_hashes = os.path.exists(f"{temp_folder}/{output_file}.hashes")
    if check_chunk_hashes:
        hashes_file = f"{temp_folder}/{output_file}.hashes"
        if os.path.exists(hashes_file):
            with open(hashes_file, "r") as f:
                chunk_hashes = f.read().splitlines()
        else:
            return jsonify({"error": "Hashes file does not exist"})
    
    # Process the files (reconstruct the file)
    try:
        chunks = [chunk for chunk in files if not chunk.endswith(".hash") and not chunk.endswith(".hashes")]
        chunks.sort()

        with open(f"{UPLOAD_FOLDER}/{userid}/{output_file}", "wb") as f:
            for i, chunk in enumerate(chunks):
                with open(f"{temp_folder}/{chunk}", "rb") as chunk_file:
                    chunk_data = chunk_file.read()

                    # Verify chunk hash if enabled
                    if check_chunk_hashes:
                        chunk_hash_obj = hashlib.sha256()
                        chunk_hash_obj.update(chunk_data)
                        chunk_hash = chunk_hash_obj.hexdigest()
                        if chunk_hashes and chunk_hash != chunk_hashes[i]:
                            return jsonify({"error": f"Chunk {i} hash mismatch! Expected {chunk_hashes[i]}, got {chunk_hash}."})

                    f.write(chunk_data)

        # Verify file-wide hash
        if check_hash and hash_value:
            with open(f"{UPLOAD_FOLDER}/{userid}/{output_file}", "rb") as f:
                data = f.read()
                file_hash_obj = hashlib.sha256()
                file_hash_obj.update(data)
                file_hash = file_hash_obj.hexdigest()
                if file_hash != hash_value:
                    return jsonify({"error": "File hashes do not match!"})

        # Remove the temp folder
        #While the folder exists
        while os.path.exists(temp_folder):
            #Remove the folder
            shutil.rmtree(temp_folder)
        
        return jsonify({"success": "Files processed"})
    except Exception as e:
        return jsonify({"error": "Error processing files: " + str(e)})
    

@app.route("/cleanup", methods=["POST"])
def cleanup():
    #In the event of an error client side, the user can request to remove the temp folder.
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]

    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    # Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        return jsonify({"error": "Temp folder does not exist"})
    
    # Remove the temp folder
    shutil.rmtree(temp_folder)
    return jsonify({"success": "Temp folder removed"})

@app.route("/download", methods=["POST"])
def download():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]
    filename = request.form["filename"]

    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"}), 401

    # Check if the file exists
    file_path = os.path.join(UPLOAD_FOLDER, userid, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Create a temporary folder for the chunks
    temp_folder = os.path.join(UPLOAD_FOLDER, userid, tempid)
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Split the file into chunks
    chunk_size = 1024 * 1024  # 1 MB
    chunk_index = 0
    with open(file_path, "rb") as f:
        while True:
            chunk_data = f.read(chunk_size)
            if not chunk_data:
                break
            chunk_filename = os.path.join(temp_folder, f"{filename}.{chunk_index}")
            with open(chunk_filename, "wb") as chunk_file:
                chunk_file.write(chunk_data)
            chunk_index += 1

    # Stream the chunks to the client
    def generate():
        for index in range(chunk_index):
            chunk_filename = os.path.join(temp_folder, f"{filename}.{index}")
            with open(chunk_filename, "rb") as chunk_file:
                yield chunk_file.read()
            os.remove(chunk_filename)  # Remove the chunk after sending

        # Remove the temporary folder
        os.rmdir(temp_folder)

    return app.response_class(generate(), mimetype="application/octet-stream")

@app.route("/get_hash", methods=["POST"])
def get_hash():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    filename = request.form["filename"]

    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        print("Unauthorized")
        return jsonify({"error": "Unauthorized"}), 401

    # Check if the file exists
    file_path = os.path.join(UPLOAD_FOLDER, userid, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    

    # Calculate the hash of the file
    file_hash_obj = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read()
        file_hash_obj.update(data)
        file_hash = file_hash_obj.hexdigest()

    return jsonify({"hash": file_hash})

if __name__ == "__main__":
    app.run(port=5000)