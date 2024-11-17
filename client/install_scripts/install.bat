@echo off
echo Setting up MacBook Cloud Storage client...

:: Step 1: Download client scripts
echo Downloading upload.py...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/upload.py

echo Downloading download.py...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/download.py

echo Downloading requirements.txt...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/requirements.txt

echo Downloading manager.py...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/client/manager.py

:: Step 2: Check if Python is installed
echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

:: Step 3: Install required Python libraries
echo Installing Python requirements...
pip install -r requirements.txt

:: Step 4: Prompt for configuration
echo Configuring client environment variables...
set /p username=Enter your username: 
setx C_DOWNLOADER_USERNAME %username%

set /p token=Enter your auth token: 
setx C_DOWNLOADER_AUTH_TOKEN %token%

set /p server_url=Enter the server URL: 
setx C_DOWNLOADER_SERVER_URL %server_url%

:: Step 5: Create aliases for upload, download, and shell
echo Creating command aliases...

:: Create cupload.bat
(
    echo @echo off
    echo python "%~dp0upload.py" %%*
) > cupload.bat
move cupload.bat %~dp0\cupload.bat

:: Create cdownload.bat
(
    echo @echo off
    echo python "%~dp0download.py" %%*
) > cdownload.bat
move cdownload.bat %~dp0\cdownload.bat

:: Create cshell.bat
(
    echo @echo off
    echo python "%~dp0manager.py" %%*
) > cshell.bat
move cshell.bat %~dp0\cshell.bat

:: Add current directory to PATH
echo Adding current directory to PATH...
setx PATH "%~dp0;%PATH%"

echo Setup complete! You can now use the following commands:
echo - "cupload {filename} {args}" to upload files
echo - "cdownload {filename} {args}" to download files
echo - "cshell {args}" to run the manager shell

pause
