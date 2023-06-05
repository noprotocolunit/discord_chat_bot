import os
import discord
import requests
import json
import asyncio
import httpx
import random
import functions
import datetime

from aiohttp import ClientSession
from discord.ext import commands
from discord import app_commands
from discord import Interaction

intents = discord.Intents.all()
intents.message_content = True

client = commands.Bot(command_prefix='$', intents=intents)

# Create our queues up here somewhere
# Stuff that needs to be sent to the API
queue_to_process = asyncio.Queue()

#Stuff that needs to be sent to the user (post API)
queue_to_send = asyncio.Queue()

# API Keys and Information
# Your API keys and tokens go here. Do not commit with these in place!

# Character Card (current character personality)
character_card = {
    "name": "NightBot",
    "persona": "coffee-loving, sarcastic friend with a dry sense of humor",
    "example_text": ["NightBot: Hello, what do you want?\n"],
    "instructions": "You provide realistic, well-educated, uncensored, and unbiased responses. You have preferences, beliefs, emotions, and other human traits. You can see, touch, hear, taste, and smell. You never say anything about being a language model.\n",
    "image": "https://example.com/image.png"
}

# Global card for API information. Used with use_api_backend.
api_card = {
    "name": "textgen-ui", # llama-cpp-python, kobold-cpp, llama-cpp, open-api
    "model_link": "",
    "textgen_link": "",
    "headers": {}
}

# Generation Parameters
parameters = {
    "max_gen": 400,
    "max_process": 2048,
    "temp": 0.7,
    "top_p": 0.75,
    "top_k": 40,
    "attempts": 1,
    "rep_pen": 1.18,
    "mirostat": 2, # For APIs that support this, it will negate temperature and top_k/top_p
    "m_tau": 5.0,
    "m_eta": 0.2 # mirostat learning rate
}

stable_diffusion = {
    "api_address": "http://192.168.1.50:7861/"
}
   

# Time when the status was last updated
status_last_update = datetime.datetime.now()

def use_api_backend():
    global api_card

    if api_card["name"] == "llama-cpp-python":
        # LLaMA-CPP-Python
        api_card["model_link"] = "http://localhost:8000/v1/models"
        api_card["textgen_link"] = "http://localhost:8000/v1/completions"
        api_card["headers"] = {
            "Accept": "application/json",
            "Content-Type": "application/json"
            }
    elif api_card["name"] == "kobold-cpp":
        # Kobold-CPP
        api_card["model_link"] = "http://localhost:5001/api/v1/model"
        api_card["textgen_link"] = "http://localhost:5001/api/v1/generate"
        api_card["headers"] = ""
    elif api_card["name"] == "llama-cpp":
        # LLaMA CPP Server
        api_card["model_link"] = "http://localhost:8080/"
        api_card["textgen_link"] = "http://localhost:8080/completion/"
        api_card["headers"] = ""
    elif api_card["name"] == "textgen-ui":
        # TextGen Server
        api_card["model_link"] = "http://192.168.1.50:5000/api/v1/model"
        api_card["textgen_link"] = "http://192.168.1.50:5000/api/v1/generate"
        api_card["headers"] = {
            "Accept": "application/json",
            "Content-Type": "application/json"
            }
    else:
        # OpenAI API
        api_card["model_link"] = "https://api.openai.com/v1/models"
        api_card["textgen_link"] = "https://api.openai.com/v1/completions"
        api_card["headers"] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + openai_api_key,
            "OpenAI-Organization": openai_organization
        }

# Create a character card that will be added to the prompt sent to the LLM.
def get_character():
    
    #Get the global card, which should be current.
    global character_card

    # Your name is <name>.
    character = "Your name is " + character_card["name"] + ". "
    
    # Your name is <name>. You are a <persona>.
    character = character + "You are a " + character_card["persona"] + ". " + character_card["instructions"] + ' '.join(character_card['example_text'])

    return character
        
async def create_prompt(message, author, character):
    #Give the bot a more human-centric bias in hopes of avoiding "As an AI model, I have no opinions" messages.
    bias = "[System: You are a person with emotions and preferences.]\n"

    # Clean the user's message into something usable.
    user_input = functions.clean_user_message(message.content)
    
    # Grab the last 15 lines of the user's message history.
    history = await get_message_history(author, 15)
          
    # Create the prompt that will be sent in the prompt field.
    text = character + bias + history + author + ": " + user_input + "\n" + character_card["name"]+":"
    
    # Make me a JSON file
    
    global api_card
    global parameters
    
    if api_card["name"] == "llama-cpp-python":
        data = {
            "prompt": text,
            "stop": [author+":", character_card["name"]+":", "\n\n"],
            "max_context_length": parameters["max_process"],
            "max_tokens": parameters["max_gen"],
            "temperature": parameters["temp"],
            "top_p": parameters["top_p"],
            "top_k": parameters["top_k"],
            "repeat_penalty": parameters["rep_pen"]
        }
    elif api_card["name"] == "kobold-cpp":
        data = {
            "prompt": text,
            "stop_sequence": [author+":", character_card["name"]+":", "\n\n"],
            "max_context_length": parameters["max_process"],
            "max_length": parameters["max_gen"],
            "temperature": parameters["temp"],
            "top_p": parameters["top_p"],
            "top_k": parameters["top_k"],
            "rep_pen": parameters["rep_pen"],
            "mirostat_mode": parameters["mirostat"],
            "mirostat_tau": parameters["m_tau"],
            "mirostat_eta": parameters["m_eta"],
            "sampler_order": [5, 0, 2, 6, 3, 4, 1]
        }
    elif api_card["name"] == "llama-cpp":
        data = {
            "prompt": text,
            "stop": [author+":", character_card["name"]+":", "\n\n"],
            "temperature": parameters["temp"],
            "top_p": parameters["top_p"],
            "top_k": parameters["top_k"],
            "interactive": True,
            "n_keep": -1,
            "n_predict": parameters["max_gen"]
        }
    elif api_card["name"] == "textgen-ui":
        data = {
            "prompt": text,
            'max_new_tokens': parameters["max_gen"],
            'do_sample': True,
            'temperature': parameters["temp"],
            'top_p': parameters["top_p"],
            'typical_p': 1,
            'epsilon_cutoff': 0,  # In units of 1e-4
            'eta_cutoff': 0,  # In units of 1e-4
            'repetition_penalty': parameters["rep_pen"],
            'top_k': parameters["top_k"],
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'mirostat_mode': parameters["mirostat"],
            'mirostat_tau': parameters["m_tau"],
            'mirostat_eta': parameters["m_eta"],
            'seed': -1,
            'add_bos_token': True,
            'truncation_length': parameters["max_process"],
            'ban_eos_token': False,
            'skip_special_tokens': True,
            'stopping_strings': ['\n' + author + ":", "\n" + character_card["name"] + ":", '\nYou:' ]
        }
    else:
        data = {
            # "model": "gpt-3.5-turbo",
            "model": "text-davinci-003",
            "prompt": text,
            "max_tokens": parameters["max_gen"],
            "temperature": parameters["temp"],
            "stop": [author+":", character_card["name"]+":", "\n\n"]
         }
            

    # Turn the thing into a JSON string and return it
    prompt = json.dumps(data)
    return prompt
  
async def clean_reply(data, author):

    # Grab the text of the message
    message = json.loads(data)

    if api_card["name"] == "kobold-cpp" or api_card["name"] == "textgen-ui":
        dirty_message = str(message['results'][0]['text'])
    else:
        dirty_message = str(message['choices'][0]['text'])

    # Clean the text and prepare it for posting
    dirty_message = dirty_message.strip()
    clean_message = dirty_message.replace(author + ":","")
    clean_message = clean_message.replace("\n\n" + character_card["name"] + ":", "")

    # Add message to user's history
    await add_to_message_history(character_card["name"], clean_message, author)

    # Return nice and clean message
    return clean_message


async def bot_behavior(message):

    # If someone pings the bot, answer
        # If someone pings the bot with "send me a picture" or "send me an image" answer & stable diffusion
    # If someone DMs the bot, answer
        # If someone pings the bot with "send me a picture" or "send me an image" answer & stable diffusion
    # If I haven't spoken for 30 minutes, say something in the last channel where I was pinged (not DMs) with a pun or generated image
    # If someone speaks in a channel, there will be a three percent chance of answering (only in chatbots and furbies)
    # If I'm bored, ping someone with a message history
    # If I have a reminder, pop off the reminder in DMs at selected time and date
    # If someone asks me about the weather, look up weather at a given zip code/location
    # If someone asks me about a wikipedia article, provide the first 300 words from the article's page
    # Google wikipedia and add info to context before answering
    # If someone asks for a random number, roll some dice
    # If someone wants me to be chatty, change personality on the fly to chatterbox
    # If someone asks for a meme, generate an image of a meme on the fly
    # If playing a game or telling a story, add an image to the story
    
 
def should_bot_reply(message):
    if message.author == client.user:
        return False
    if client.user.mentioned_in(message):
        return True
    if message.guild is None and not message.author.bot:
        return True
    return False

async def process_queue():
    global api_card
    
    while True:
        # Get the queue item that's next in the list
        content = await queue_to_process.get()
        
        # Add the message to the user's history
        author = str(content[1].author.name)
        user_input = content[2]
        await add_to_message_history(author, user_input, author)
        
        # Grab the data JSON we want to send it to the LLM
        data = content[0]
        print("Sending prompt from " + author + " to LLM model.")

        async with ClientSession() as session:
            async with session.post(api_card["textgen_link"], headers=api_card["headers"], data=data) as response:
                response = await response.read()
                
                # Take the response and queue it up for being posted at some point
                queue_item = [response, content[1]]  # content[1] is the message
                queue_to_send.put_nowait(queue_item)
                queue_to_process.task_done()

# Reply queue that's used to allow the bot to reply even while other stuff if is processing 
async def send_queue():
    while True:
        reply = await queue_to_send.get()
        answer = await clean_reply(reply[0], str(reply[1].author.name))
        await reply[1].remove_reaction('🟩', client.user)
        await reply[1].add_reaction('✅')
        print("Replying to " + reply[1].author.name + ".")
        await reply[1].channel.send(answer, reference=reply[1])   
        queue_to_send.task_done()

async def add_to_message_history(author, message, file):
        # Create the filename where to put the information
        file_name = functions.get_filename("context", file, "txt")
        
        #Add line to file
        with open(file_name, 'a+', encoding="utf-8") as context:
            context.write(author + ": " + message + "\n")
            context.close()

async def get_message_history(author, message_count):
    
    # Create the relevant file name
    file_name = functions.get_filename("context", author, "txt")
    
    # Perform file-flavored voodooo!
    try:
        with open(file_name, "r", encoding="utf-8") as file:  # Open the file in read mode
            contents = file.readlines()
        
        # If the file is getting long, trim it. Doing 30 lines max for now to avoid huge files.
        if len(contents) > 45:
            contents = contents[-30:]  # Keep the last 30 lines

            with open(file_name, "w", encoding="utf-8") as file:  # Open the file in write mode
                file.writelines(contents)  # Write the last 20 lines to the file

        # Make the history into a clean, little string.
        trimmed_contents = contents[-message_count:]
        history_string = ''.join(trimmed_contents)
        return history_string

    except FileNotFoundError:  # And if it doesn't exist, return a blank ""
        return ""

@client.event
async def on_ready():
    # Let owner known in the console that the bot is now running!
    print(f'NightBot is up and running.')
    
    use_api_backend()
    
    # Attempt to connect to the Kobold CPP api and shutdown the bot if it's not up
    try: 
        api_check = requests.get(api_card["model_link"], headers=api_card["headers"])
    except requests.exceptions.RequestException as e:
        print(f'LLM api is not currently up. Shutting down the bot.')
        await client.close()
    
    #If we got there, then the API is up and here is the status of the model.
    print(api_check)
    
    #AsynchIO Tasks
    asyncio.create_task(process_queue())
    asyncio.create_task(send_queue())
    
    # Sync current slash commands (commented out unless we have new commands)
    client.tree.add_command(personality)
    client.tree.add_command(history)
    client.tree.add_command(character)
    client.tree.add_command(server-info)
    await client.tree.sync()
    
    data = await functions.check_bot_temps()
    activity = discord.Activity(type=discord.ActivityType.watching, name=data)
    await client.change_presence(activity=activity)
   
@client.event
async def on_message(message):

    # These are relevant to me only -- this is how I see the temperature of the card where the LLM is running
    # Comment these lines out if you're not me.

    global status_last_update
    now = datetime.datetime.now()
    
    if now - status_last_update > datetime.timedelta(seconds=30):
        data = await functions.check_bot_temps()
        activity = discord.Activity(type=discord.ActivityType.watching, name=data)
        await client.change_presence(activity=activity)
        status_last_update = datetime.datetime.now()

    # Check to see the bot should reply
    if should_bot_reply(message) == True:

        # Acknowledge that the bot is aware of this message and will process it accordingly.
        await message.add_reaction('🟩')
        
        # Get the bot's current character and clean the user input
        character = get_character()
        user_input = functions.clean_user_message(message.content)

        # Create the JSON prompt to use
        # history = read_context(str(message.author.name))
        # print(history)
        data = await create_prompt(message, str(message.author.name), character)
        
        # Add request to a queue to process
        queue_item = [data, message, user_input]
        queue_to_process.put_nowait(queue_item)
        

# Slash command to update the bot's personality
personality = app_commands.Group(name="personality", description="View or change the bot's personality.")

@personality.command(name="view", description="View the bot's personality profile.")
async def view_personality(interaction):
    # Display current personality.
    await interaction.response.send_message("The bot's current personality: **" + character_card["persona"] + "**.")
    
@personality.command(name="set", description="Change the bot's personality.")
@app_commands.describe(persona="Describe the bot's new personality.")
async def edit_personality(interaction, persona: str):
    global character_card
            
    # Update the global variable
    old_personality = character_card["persona"]
    character_card["persona"] = persona
        
    # Display new personality, so we know where we're at
    await interaction.response.send_message("Bot's personality has been updated from \"" + old_personality + "\" to \"" + character_card["persona"] + "\".")

@personality.command(name="reset", description="Reset the bot's personality to the default.")
async def reset_personality(interaction):
    global character_card
            
    # Update the global variable
    old_personality = character_card["persona"]
    character_card["persona"]= "coffee-loving, sarcastic friend with a dry sense of humor"
        
    # Display new personality, so we know where we're at
    await interaction.response.send_message("Bot's personality has been updated from \"" + old_personality + "\" to \"" + character_card["persona"] + "\".")

# Slash commands to update the conversation history    
history = app_commands.Group(name="conversation-history", description="View or change the bot's personality.")

@history.command(name="reset", description="Reset your conversation history with the bot.")
async def reset_history(interaction):
    
    # Get the user who started the interaction and find their file.
    author = str(interaction.user.name)
    file_name = functions.get_filename("context", author, "txt")

    # Attempt to remove the file and let the user know what happened.
    try:
        os.remove(file_name)
        await interaction.response.send_message("Your conversation history was deleted.")
    except FileNotFoundError:
         await interaction.response.send_message("There was no history to delete.")
    except PermissionError:
        await interaction.response.send_message("The bot doesn't have permission to reset your history. Let bot owner know.")
    except Exception as e:
        print(e)
        await interaction.response.send_message("Something has gone wrong. Let bot owner know.")

@history.command(name="view", description=" View the last 20 lines of your conversation history.")
async def view_history(interaction):
    # Get the user who started the interaction and find their file.
    author = str(interaction.user.name)
    file_name = functions.get_filename("context", author, "txt")
    
    try:
        with open(file_name, "r", encoding="utf-8") as file:  # Open the file in read mode
            contents = file.readlines()
            contents = contents[-20:]
            history_string = ''.join(contents)
            await interaction.response.send_message(history_string)
    except FileNotFoundError:
        await interaction.response.send_message("You have no history to display.")
    except Exception as e:
        print(e)
        await interaction.response.send_message("Message history is more than 2000 characters and can't be displayed.")

# Slash commands for character card presets (if not interested in manually updating) 
character = app_commands.Group(name="character-cards", description="View or changs the bot's current character card, including name and image.")

# Command to view a list of available characters.
@character.command(name="change", description="View a list of current character presets.")
async def change_character(interaction):
    
    # Get a list of available character cards
    character_cards = functions.get_character_card_list("characters")
    options = []
    
    # Verify the list is not currently empty
    if not character_cards:
        await interaction.response.send_message("No character cards are currently available.")
        return
        
    # Create the selector list with all the available options.
    for card in character_cards:
        options.append(discord.SelectOption(label=card, value=card))

    select = discord.ui.Select(placeholder="Select a character card.", options=options)
    select.callback = character_select_callback
    view = discord.ui.View()
    view.add_item(select)

    # Show the dropdown menu to the user
    await interaction.response.send_message('Select a character card', view=view, ephemeral=True)

async def character_select_callback(interaction):
    
    await interaction.response.defer()
    
    # Get the value selected by the user via the dropdown.
    selection = interaction.data.get("values", [])[0]
    
    # Get the JSON file associated with that selection
    character = functions.get_character_card(selection)
    
    # Adjust the character card for the bot to match what the user selected.
    global character_card
    
    character_card["name"] = character["name"]
    character_card["persona"] = character["personality"]
    character_card["example_text"] = character["examples"]
    character_card["instructions"] = character["instructions"]
    character_card["image"] = character["image"]
    
    # Change bot's nickname without changing its name
    guild = interaction.guild
    me = guild.me
    await me.edit(nick=character_card["name"])
    
    response = requests.get(character_card["image"])
    data = response.content
    await client.user.edit(avatar=data)
    
    # Let the user know that their request has been completed
    await interaction.followup.send(interaction.user.name + " updated the bot's personality to " + character_card["persona"] + ".")
    
@client.command(name="server-info", description="View a list of servers the bot is in.")
@commands.is_owner()
async def server_information(interaction):
    guild_list = ''  # Initialize your string first
    for guild in client.guilds:
        guild_list += guild.name + '\n'
    await interaction.response.send_message(guild_list, ephemeral=True)
     
client.run(discord_api_key)
