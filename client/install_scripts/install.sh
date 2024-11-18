#!/bin/bash

echo "Setting up MacBook Cloud Storage client..."

# Step 1: Download client scripts
echo "Downloading upload.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/client/upload.py

echo "Downloading download.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/client/download.py

echo "Downloading requirements.txt..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/client/requirements.txt

echo "Downloading manager.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MacBook-Cloud-Storage/refs/heads/main/client/manager.py

# Step 2: Check if Python is installed
echo "Checking if Python is installed..."
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python and try again."
    exit 1
fi

# Step 3: Install required Python libraries
echo "Installing Python requirements..."
pip3 install -r requirements.txt || { echo "Failed to install requirements. Check your Python and pip installation."; exit 1; }

# Step 4: Prompt for configuration
echo "Configuring client environment variables..."
read -p "Enter your username: " username
export C_DOWNLOADER_USERNAME="$username"
echo "export C_DOWNLOADER_USERNAME=\"$username\"" >> ~/.bashrc

read -p "Enter your auth token: " token
export C_DOWNLOADER_AUTH_TOKEN="$token"
echo "export C_DOWNLOADER_AUTH_TOKEN=\"$token\"" >> ~/.bashrc

read -p "Enter the server URL: " server_url
export C_DOWNLOADER_SERVER_URL="$server_url"
echo "export C_DOWNLOADER_SERVER_URL=\"$server_url\"" >> ~/.bashrc

# Step 5: Create aliases for upload, download, and shell
echo "Creating command aliases..."

# Create cupload script
cat <<EOL > cupload
#!/bin/bash
python3 "$(pwd)/upload.py" "\$@"
EOL
chmod +x cupload
mv cupload /usr/local/bin/cupload

# Create cdownload script
cat <<EOL > cdownload
#!/bin/bash
python3 "$(pwd)/download.py" "\$@"
EOL
chmod +x cdownload
mv cdownload /usr/local/bin/cdownload

# Create cshell script
cat <<EOL > cshell
#!/bin/bash
python3 "$(pwd)/manager.py" "\$@"
EOL
chmod +x cshell
mv cshell /usr/local/bin/cshell

# Refresh shell environment
source ~/.bashrc

echo "Setup complete! You can now use the following commands:"
echo " - 'cupload {filename} {args}' to upload files"
echo " - 'cdownload {filename} {args}' to download files"
echo " - 'cshell {args}' to run the manager shell"

echo "Restart your terminal for the environment variables to take effect."
