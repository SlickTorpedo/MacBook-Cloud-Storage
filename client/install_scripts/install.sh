#!/bin/bash

echo "Setting up MacBook Cloud Storage client..."

# Step 1: Download client scripts
echo "Downloading upload.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/upload.py

echo "Downloading download.py..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/download.py

echo "Downloading requirements.txt..."
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/requirements.txt

# Step 2: Check if Python is installed
echo "Checking if Python is installed..."
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python 3 and try again."
    exit 1
fi

# Step 3: Install required Python libraries
echo "Installing Python requirements..."
pip3 install -r requirements.txt

# Step 4: Prompt for configuration
echo "Configuring client environment variables..."
read -p "Enter your username: " username
export C_DOWNLOADER_USERNAME=$username
echo "export C_DOWNLOADER_USERNAME=$username" >> ~/.bashrc

read -p "Enter your auth token: " token
export C_DOWNLOADER_AUTH_TOKEN=$token
echo "export C_DOWNLOADER_AUTH_TOKEN=$token" >> ~/.bashrc

read -p "Enter the server URL: " server_url
export C_DOWNLOADER_SERVER_URL=$server_url
echo "export C_DOWNLOADER_SERVER_URL=$server_url" >> ~/.bashrc

# Step 5: Create aliases for upload and download
echo "Creating command aliases..."

# Create cupload script
cat << EOF > cupload
#!/bin/bash
python3 $(pwd)/upload.py "\$@"
EOF
chmod +x cupload
sudo mv cupload /usr/local/bin/

# Create cdownload script
cat << EOF > cdownload
#!/bin/bash
python3 $(pwd)/download.py "\$@"
EOF
chmod +x cdownload
sudo mv cdownload /usr/local/bin/

# Step 6: Reload shell configuration
shell_name=$(basename "$SHELL")

if [ "$shell_name" = "bash" ]; then
    echo "Reloading bash configuration..."
    source ~/.bashrc
elif [ "$shell_name" = "zsh" ]; then
    echo "Reloading zsh configuration..."
    source ~/.zshrc
else
    echo "Setup complete! Please restart your terminal or reload your shell configuration to apply changes."
fi

# Step 7: Final Message
echo "Setup complete! You can now use the following commands:"
echo "- 'cupload {filename} {args}' to upload files"
echo "- 'cdownload {filename} {args}' to download files"
