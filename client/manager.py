import argparse
import requests
import os
import sys
import subprocess
from dotenv import load_dotenv
from colorama import init, Fore, Style

load_dotenv()
init(autoreset=True)

DEBUG = False

def list_files(username, auth_token):
    data = {"userid": username, "auth_token": auth_token}
    response = requests.post("{}/list".format(SERVER_URL), data=data)
    if response.status_code == 404:
        return {"error": "No files found"}
    if DEBUG:
        print(response.json())
    return response.json()

def delete_file(username, auth_token, filename):
    data = {"userid": username, "auth_token": auth_token, "filename": filename}
    response = requests.post("{}/delete".format(SERVER_URL), data=data)
    if response.status_code == 404:
        return {"error": "File not found"}
    if DEBUG:
        print(response.json())
    return response.json()

def rename_file(username, auth_token, old_filename, new_filename):
    data = {"userid": username, "auth_token": auth_token, "old_filename": old_filename, "new_filename": new_filename}
    response = requests.post("{}/rename".format(SERVER_URL), data=data)
    if response.status_code == 404:
        return {"error": "File not found"}
    if DEBUG:
        print(response.json())
    return response.json()

def run_script(script_name, args):
    command = [sys.executable, script_name] + args
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        print(line, end='')
    process.stdout.close()
    process.wait()
    return process.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage files on the server.")
    parser.add_argument("--username", help="The username of the user.")
    parser.add_argument("--auth_token", help="The authentication token of the user.")
    parser.add_argument("--server_url", help="The server URL.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    USERNAME = args.username or os.getenv('C_DOWNLOADER_USERNAME')
    AUTH_TOKEN = args.auth_token or os.getenv('C_DOWNLOADER_AUTH_TOKEN')
    SERVER_URL = args.server_url or os.getenv('C_DOWNLOADER_SERVER_URL') or "http://localhost:5000"
    DEBUG = args.debug

    if not USERNAME or not AUTH_TOKEN:
        print(Fore.RED + "Username and auth token must be provided either as arguments or environment variables. Please set ENV variables C_DOWNLOADER_USERNAME and C_DOWNLOADER_AUTH_TOKEN.")
        sys.exit(1)

    while True:
        command = input(Fore.CYAN + "Enter command (ls, mv filename newfilename, rm filename, up filename, down filename, exit): ").strip()
        if command == "ls":
            files = list_files(USERNAME, AUTH_TOKEN)
            if "error" in files:
                print(Fore.RED + files["error"])
            else:
                files = files["files"]
                print(Fore.GREEN + "Files on server:")
                files_on_server = ""
                for f in files:
                    files_on_server += f + "   "
                print(Fore.GREEN + files_on_server)
        elif command.startswith("mv "):
            parts = command.split()
            if len(parts) == 3:
                old_filename, new_filename = parts[1], parts[2]
                response = rename_file(USERNAME, AUTH_TOKEN, old_filename, new_filename)
                if response.get("error"):
                    print(Fore.RED + f"Error renaming file: {response.get('error')}")
                else:
                    print(Fore.GREEN + f"File {old_filename} renamed to {new_filename} successfully.")
            else:
                print(Fore.YELLOW + "Invalid command format. Use: mv filename newfilename")
        elif command.startswith("rm "):
            parts = command.split()
            if len(parts) == 2:
                filename = parts[1]
                response = delete_file(USERNAME, AUTH_TOKEN, filename)
                if response.get("error"):
                    print(Fore.RED + f"Error deleting file: {response.get('error')}")
                else:
                    print(Fore.GREEN + f"File {filename} deleted successfully.")
            else:
                print(Fore.YELLOW + "Invalid command format. Use: rm filename")
        elif command.startswith("up "):
            args = command.split()[1:]
            run_script("cupload", args)
        elif command.startswith("down "):
            args = command.split()[1:]
            run_script("cdownload", args)
        elif command == "exit":
            break
        else:
            print(Fore.YELLOW + "Invalid command. Use: ls, mv filename newfilename, rm filename, up filename, down filename, exit")