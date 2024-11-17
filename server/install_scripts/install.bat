@echo off
echo Setting up MacBook Cloud Storage server...

:: Step 1: Download app.py
echo Downloading app.py...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/server/app.py

:: Step 2: Download requirements.txt
echo Downloading requirements.txt...
curl -O https://raw.githubusercontent.com/SlickTorpedo/MackBook-Cloud-Storage/refs/heads/main/server/requirements.txt

:: Step 3: Check if Python is installed
echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

:: Step 4: Install required Python libraries
echo Installing Python requirements...
pip install -r requirements.txt

:: Step 5: Prompt for user credentials
echo Please create a new user for the server.
set /p username=Enter a username: 
set /p token=Enter an auth token: 

:: Step 6: Create the .env file
echo Creating .env file...
(
    echo USERS={^"%username%":"%token%"^}
) > .env

:: Step 7: Run the application
echo Setup complete. Starting the server...
python app.py

pause
