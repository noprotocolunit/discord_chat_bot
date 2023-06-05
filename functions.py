import json
import os
import asyncio
import base64

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

# A function for separating images from text that returns both.    
def separate_image_text(message)
    
    # Locates the image based on what's provided
    img_start = message.find("<img")
    img_end = message.find(">") + 1
    
    # If there's an image in there, separates it
    if img_start != -1:
        img_tag = message[img_start:img_end]
        text = message[img_end:].strip()
    else:
        img_tag = None
        text = message.strip()

    print(text)
    return img_tag, text