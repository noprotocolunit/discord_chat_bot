import json
import os


def get_filename(directory, file, extension):
    return directory + "\\" + file + "." + extension

# Get the contents of a character file (which should contain everything about the character)
def get_character_card(name):
    
    #Get the name of the file we'll be using
    file = "characters\\" + name
    
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