import json
import os
import asyncio
import re
import base64
from PIL import Image
import io

def get_filename(directory, file, extension):
    return directory + "\\" + file + "." + extension

# Get the contents of a character file (which should contain everything about the character)
def get_character_card(name):
    
    #Get the name of the file we'll be using
    file = os.path.join("characters", name)
    
    # Open the file and load its contents into a JSON
    with open(file, 'r') as file:
        character = json.load(file)
    
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

# Clean the input provided by the user to the bot!
def clean_user_message(user_input):

    # Remove the bot's tag from the input since it's not needed.
    user_input = user_input.replace("<@1080950961268342874>","")
    
    # Remove any spaces before and after the text.
    user_input = user_input.strip()
    
    return user_input

# A function for checking bot's temperature (lterally, card temps)
async def check_bot_temps():
    process = await asyncio.create_subprocess_exec("powershell.exe", "S:\AI\extra_scripts\strippedinfo.ps1", stdout=asyncio.subprocess.PIPE)
    output, _ = await process.communicate()
    return output.decode()
 
