#Flask app for accepting the files and returning the results.
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import math
import hashlib

app = Flask(__name__)
CORS(app)

#This operates on a user system, so each user gets a folder with their files.
#The "uploads" folder contains all the files uploaded by all users.
UPLOAD_FOLDER = "uploads"

def authorize_user(userid, auth_token):
    if(userid != "test" or auth_token != "test"):
        return False
    #Check if the user is authorized to upload files.
    return True

#When a user uploads a file, it will contain a "tempid" field.
#THis tempid is used as the folder name for the user while the file is being processed.
#Then, once the file is processed, the file is saved in the users folder with the proper filename, and the tempid folder is deleted.
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
    
    #Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    #Create a folder for the user if it doesn't exist
    user_folder = f"{UPLOAD_FOLDER}/{userid}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    #Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    else:
        #This should not happen, as the tempid should be unique
        #The client will generate a unique ID, and send it to the /id endpoint to check if it is unique.
        return jsonify({"error": "Temp folder already exists"})
    
    #Save the file to the temp folder
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
    
    #Check if the user is authenticated
    if not authorize_user(userid, auth_token):
        return jsonify({"error": "Unauthorized"})
    
    #Check if the tempid folder exists
    temp_folder = f"{UPLOAD_FOLDER}/{userid}/{tempid}"
    if not os.path.exists(temp_folder):
        return jsonify({"success": "ID is unique"})
    else:
        return jsonify({"error": "ID already exists"})

if __name__ == "__main__":
    app.run(port=5000)
