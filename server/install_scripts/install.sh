#!/bin/bash

echo "Setting up MacBook Cloud Storage server..."

# Step 1: Download app.py
echo "Downloading app.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/server/app.py

# Step 2: Download requirements.txt
echo "Downloading requirements.txt..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/server/requirements.txt

# Step 3: Check if Python is installed
echo "Checking if Python is installed..."
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python 3 and try again."
    exit 1
fi

# Step 4: Install required Python libraries
echo "Installing Python requirements..."
pip3 install -r requirements.txt

# Step 5: Prompt for user credentials
echo "Please create a new user for the server."
read -p "Enter a username: " username
read -p "Enter an auth token: " token

# Step 6: Create the .env file
echo "Creating .env file..."
echo "USERS={\"$username\":\"$token\"}" > .env

# Step 7: Run the application
echo "Setup complete. Starting the server..."
python3 app.py
