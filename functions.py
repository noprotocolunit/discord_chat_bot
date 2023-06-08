import json
import requests 
import os
import asyncio
import re
import base64
from PIL import Image
import io
from datetime

   
# Get the full path of a file and hand it over
# Does this need any kind of error handling? 
def get_file_name(directory, file_name):

    # Create the file path from name and directory and return that information
    filepath = os.path.join(directory, file_name)
    return filepath

# Read in a JSON file and spit it out, usefully or "None" if file's not there or we have an issue 
# Returns a JSON file
def get_json_file(filename):

    # Try to go read the file!
    try:
        with open(filename, 'r') as file:
             contents = json.load(file)
             return contents
    # Be very sad if the file isn't there to read
    except FileNotFoundError:
        await write_to_log("File " + filename + "not found. Where did you lose it?")
        return None
    # Be also sad if the file isn't a JSON or is malformed somehow
    except json.JSONDecodeError:
        await write_to_log("Unable to parse " + filename + " as JSON.")
        return None
    # Be super sad if we have no idea what's going on here
    except Exception as e:
        await write_to_log("An unexpected error occurred: " + e)
        return None

# Read in however many lines of a text file (for context or other text)
# Returns a string with the contents of the file
def get_txt_file(filename, lines):

    # Attempt to read the file and put its contents into a variable
    try:
        with open(file_name, "r", encoding="utf-8") as file:  # Open the file in read mode
            contents = file.readlines()
            contents = contents[-lines:]
            
            # Turn contents into a string for easier consumption
            # I may not want to do this step. We'll see
            history_string = ''.join(contents)
            return history_string
    # Let someone know if the file isn't where we expected to find it.
    except FileNotFoundError:
        await write_to_log("File " + filename + " not found. Where did you lose it?")
        return None
    # Panic if we have no idea what's going in here
    except Exception as e:
        await write_to_log("An unexpected error occurred: " + e)
        return None

# Get the contents of a character file (which should contain everything about the character)
def get_character_card(name):

    # Get the file name and then its contents
    file = get_file_name("characters", name)
    contents = get_json_file(file)
    
    if contents != None
        character.clear()
        character.update(contents)
   
    #return the contents of the JSON file
    return character
    
# Get the list of all available characters (files in the character directory, hopefully)
def get_character_card_list(directory):

    # Try to get the list of character files from the directory provided. 
    try:
        dir_path = directory + "\\"
        files = os.listdir(dir_path)
    except FileNotFoundError:
        files = []
    except OSError:
        files = []

    # Return either the list of files or a blank list.
    return files

# A function for checking bot's temperature (lterally, card temps)
async def check_bot_temps():
    process = await asyncio.create_subprocess_exec("powershell.exe", "S:\AI\extra_scripts\strippedinfo.ps1", stdout=asyncio.subprocess.PIPE)
    output, _ = await process.communicate()
    return output.decode()
    
# Figure out if the user is looking for an image to be generated    
def check_for_image_request(user_message):
    # Set user's message to all lowercase
    user_message = user_message.lower()
    
    # Create a pattern we'll be matching against
    pattern = re.compile('(send|create|give|generate|draw|snap|take|message).*?(image|picture|photo|drawing)')
    
    # Do some matching, I suppose
    result = bool(pattern.search(user_message))
    return result

# Set an API struct to whatever is in a JSON file to our heart's content
def set_api(config_file):

    # Go grab the configuration file for me
    file = get_file_name("configurations", config_file)
    contents = get_json_file(file)
    
    # If contents aren't none, clear the API and shove new data in
    if contents != None
        api.clear()
        api.update(contents)

    # Return the API
    return api

# Check to see if the API is running (pick any API)
def api_status_check(link, headers):

    try:
        response = requests.get(api_link, headers=headers)
        status = response.ok
    except requests.exceptions.RequestException as e:
        await write_to_log("Error occurred: " +e +". Language model not currently running.")
        status = False

    return status

# Write a line to the log file    
async def write_to_log(information):
    file = get_file_name("", "log.txt")
    
    # Add a time stamp to the provided error message
    current_time = datetime.datetime.now()
    rounded_time = current_time.replace(microsecond=0)
    text = str(rounded_time) + " " + information
    
    await append_text_file(file, text)

# Append text to the end of a text file
async def append_text_file(file, text):

    with open(file, 'a+', encoding="utf-8") as context:
        context.write(text)
        context.close()
        
async def prune_conversation_history(file_name, max_lines, trim_to):
    file = get_file_name("context", file_name)
    
    try:
        with open(file, "r", encoding="utf-8") as f:  # Open the file in read mode
            contents = f.readlines()
            
        if len(contents) > max_lines:
            contents = contents[-trim_to:]  # Keep the last 'trim_to' lines

        with open(file, "w", encoding="utf-8") as f:  # Open the file in write mode
            f.writelines(contents)  # Write the pruned lines to the file
    except FileNotFoundError:
        await write_to_log("Could not prune file " + file + " because it doesn't exist.")

def get_conversation_history(user):
    file = get_file_name("context", user+".txt")
    history = get_txt_file(file, 10)
    
    if history == None
        history = ""
    
    return history

async def add_to_conversation_history(message, user, file):

    file_name = functions.get_file_name("context", file + ".txt")
    content = user + ": " + message + "\n"
    await append_text_file(file_name, content)     

# Clean the input provided by the user to the bot!
def clean_user_message(user_input):

    # Remove the bot's tag from the input since it's not needed.
    user_input = user_input.replace("<@1080950961268342874>","")
    
    # Remove any spaces before and after the text.
    user_input = user_input.strip()
    
    return user_input

def get_character(character_card)

    return character