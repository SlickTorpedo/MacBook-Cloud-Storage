# Flask app for accepting the files and returning the results.
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import hashlib
import shutil

app = Flask(__name__)
CORS(app)

# This operates on a user system, so each user gets a folder with their files.
# The "uploads" folder contains all the files uploaded by all users.
UPLOAD_FOLDER = "uploads"

def authorize_user(userid, auth_token):
    if(userid != "test" or auth_token != "test"):
        return False
    # Check if the user is authorized to upload files.
    return True

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
    # else:
    #     # This should not happen, as the tempid should be unique
    #     # The client will generate a unique ID, and send it to the /id endpoint to check if it is unique.
    #     return jsonify({"error": "Temp folder already exists"})
    
    # Save the file to the temp folder
    try:
        file.save(f"{temp_folder}/{file.filename}")
        return jsonify({"success": "File uploaded"})
    except Exception as e:
        return jsonify({"error": "Error saving file: " + str(e)})
    

@app.route("/id", methods=["POST"])
def check_id():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]
    
    # Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    # Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        return jsonify({"success": "ID is unique"})
    else:
        return jsonify({"error": "ID already exists"})
    
@app.route("/process", methods=["POST"])
def process_file():
    userid = request.form["userid"]
    auth_token = request.form["auth_token"]
    tempid = request.form["tempid"]
    output_file = request.form["output_file"]
    check_hash = request.form.get("check_hash", "true").lower() == "true"
    check_chunk_hashes = request.form.get("check_chunk_hashes", "false").lower() == "true"
    
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
    if check_hash:
        hash_file = f"{temp_folder}/{output_file}.hash"
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                hash_value = f.read()
        else:
            return jsonify({"error": "Hash file does not exist"})
    
    # Read the chunk hashes
    chunk_hashes = []
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

if __name__ == "__main__":
    app.run(port=5000)