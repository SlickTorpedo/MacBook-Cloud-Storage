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

while true; do
    read -s -p "Enter your auth token: " token
    echo
    read -s -p "Confirm your auth token: " confirm_token
    echo
    if [ "$token" = "$confirm_token" ]; then
        break
    else
        echo "Tokens do not match. Please try again."
    fi
done

read -p "Enter the server URL: " server_url

# Determine the correct shell configuration file
if [ -n "$ZSH_VERSION" ]; then
    shell_rc=~/.zshrc
elif [ -n "$BASH_VERSION" ]; then
    shell_rc=~/.bashrc
else
    echo "Unsupported shell. Please manually set environment variables."
    exit 1
fi

# Export environment variables and append to the shell configuration file
echo "Exporting environment variables..."
export C_DOWNLOADER_USERNAME="$username"
export C_DOWNLOADER_AUTH_TOKEN="$token"
export C_DOWNLOADER_SERVER_URL="$server_url"

echo "export C_DOWNLOADER_USERNAME=\"$username\"" >> "$shell_rc"
echo "export C_DOWNLOADER_AUTH_TOKEN=\"$token\"" >> "$shell_rc"
echo "export C_DOWNLOADER_SERVER_URL=\"$server_url\"" >> "$shell_rc"

# Step 5: Create aliases for upload, download, and shell
echo "Creating command aliases..."

# Ensure user-level bin directory exists
mkdir -p ~/.local/bin
export PATH="$PATH:~/.local/bin"

# Create cupload script
cat <<EOL > ~/.local/bin/cupload
#!/bin/bash
python3 "$(pwd)/upload.py" "\$@"
EOL
chmod +x ~/.local/bin/cupload

# Create cdownload script
cat <<EOL > ~/.local/bin/cdownload
#!/bin/bash
python3 "$(pwd)/download.py" "\$@"
EOL
chmod +x ~/.local/bin/cdownload

# Create cshell script
cat <<EOL > ~/.local/bin/cshell
#!/bin/bash
python3 "$(pwd)/manager.py" "\$@"
EOL
chmod +x ~/.local/bin/cshell

# Add user-level bin directory to PATH if not already added
if ! grep -q "PATH=.*~/.local/bin" "$shell_rc"; then
    echo 'export PATH="$PATH:~/.local/bin"' >> "$shell_rc"
fi

# Refresh shell environment
source "$shell_rc"

echo "Setup complete! You can now use the following commands:"
echo " - 'cupload {filename} {args}' to upload files"
echo " - 'cdownload {filename} {args}' to download files"
echo " - 'cshell {args}' to run the manager shell"

echo "Restart your terminal for the environment variables to take effect."
