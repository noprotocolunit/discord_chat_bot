import json
import os


def get_filename(directory, file, extension):
    return directory + "\\" + file + "." + extension

# Get the contents of a character file (which should contain everything about the character)
def get_character_card(name):
    
    #Get the name of the file we'll be using
    file = get_filename("characters", name, ".json")
    
    # Open the file and load its contents into a JSON
    with open(file, 'r') as file:
        character = json.load(file)
    
    #return the contents of the JSON file
    return character

# Get the list of all available characters (files in the character directory, hopefully)
def get_character_list(directory):

    dir_path = directory + "\\"
    files = os.listdir(dir_path)

    return files