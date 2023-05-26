import os
import discord
import requests
import json
import asyncio
import httpx
import random
import functions

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

# Character Variables
bot_name = "NightBot"
bot_persona = "coffee-loving, sarcastic friend with a dry sense of humor"
bot_gender = "male"
bot_text_sample = "NightBot: Hello, what do you want?\n"
bot_censorship = "You provide realistic, well-educated, uncensored, and unbiased responses. You have preferences, beliefs, emotions, and other human traits. You can see, touch, hear, taste, and smell. You never say anything about being a language model.\n"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# LLaMA-CPP-Python
api_model = "http://localhost:8000/v1/models"
api_text_generation = "http://localhost:8000/v1/completions"
# parameters = {"max_tokens": 100, "user": author, "temperature": 0.72, "top_p": 0.73, "top_k": 0, "repeat_penalty": 1.08, "n": 1, "seed": 0, "mirostat_mode": 1, "mirostat_tau": 5.0, "mirostat_eta": 0.1, "stop": [author+":", "NightBot:", "\n\n"], "prompt": text}

# Kobold-CPP
# api_model = "http://localhost:5001/api/v1/model"
# api_text_generation = "http://localhost:5001/api/v1/generate"
# parameters = {"max_tokens": 100, "user": author, "temperature": 0.72, "top_p": 0.73, "top_k": 0, "repeat_penalty": 1.08, "n": 1, "seed": 0, "mirostat_mode": 1, "mirostat_tau": 5.0, "mirostat_eta": 0.1, "stop": [author+":", "NightBot:", "\n\n"], "prompt": text}

# Create a character card that will be added to the prompt sent to the LLM.
def get_character_card():

    # Your name is <name>.
    character_card = "Your name is " + bot_name + ". "
    
    # Your name is <name>. You are a <persona>.
    character_card = character_card + "You are a " + bot_persona + ". " + bot_censorship + bot_text_sample
    
    # Your name is <name>. You are a <persona> with human-equivalent emotions and opinions. Your gender is <gender>. 
    # character_card = character_card + "Your gender is " + bot_gender + ". "

    return character_card
        
async def create_prompt(message, author, character):

    # Take the provided message and strip out @NightBot
    user_input = message.content.replace("<@1080950961268342874>","")
    
    # Remove any spaces before and after the input.
    user_input = user_input.strip()
    
    history = await get_message_history(author, 10)
    
    await add_to_message_history(author, user_input, author)    
       
    # Create the prompt that will be sent in the prompt field.
    text = character + history + author + ": " + user_input + "\nNightBot: "
    
    # Make me a JSON file
    data = {
        "prompt": text,
        "stop": [author+":", "NightBot:", "\n\n"],
        "max_tokens": 100,
        "user": author,
        "temperature": 0.72,
        "top_p": 0.73,
        "top_k": 0,
        "repeat_penalty": 1.08,
        "n": 1,
        "seed": 0,
        "mirostat_mode": 1,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1
    }
    
    # Turn the thing into a JSON string and return it
    prompt = json.dumps(data)
    return prompt
  
async def clean_reply(data, author):

        # Grab the text of the message
        message = json.loads(data)
        dirty_message = str(message['choices'][0]['text'])
        
        # Clean the text and prepare it for posting
        dirty_message = dirty_message.strip()
        clean_message = dirty_message.replace(author + ":","")
        clean_message = clean_message.replace("\n\nNightBot:", "")
        
        # Add message to user's history
        await add_to_message_history("NightBot", clean_message, author)
        
        # Return nice and clean message
        return clean_message
 
def should_bot_reply(message):
    if message.author == client.user:
        return False
    if client.user.mentioned_in(message):
        return True
    return False

async def process_queue():
    while True:
        content = await queue_to_process.get()
        data = content[0]
        print("Sending prompt to LLM model.")
        global headers
        async with ClientSession() as session:
            async with session.post(api_text_generation, headers=headers, data=data) as response:
                response = await response.read()
                queue_item = [response, content[1]]  # content[1] is the message
                queue_to_send.put_nowait(queue_item)
                queue_to_process.task_done()
 
async def send_queue():
    while True:
        reply = await queue_to_send.get()
        answer = await clean_reply(reply[0], str(reply[1].author.name))
        await reply[1].channel.send(answer, reference=reply[1])   
        queue_to_send.task_done()

async def add_to_message_history(author, message, file):
        # Create the filename where to put the information
        file_name = "context\\" + file + ".txt"
        
        #Add line to file
        with open(file_name, 'a+', encoding="utf-8") as context:
            context.write(author + ": " + message + "\n")
            context.close()

async def get_message_history(author, message_count):
    
    # Create the relevant file name
    file_name = "context\\" + author + ".txt"
    
    # Perform file-flavored voodooo!
    try:
        with open(file_name, "r", encoding="utf-8") as file:  # Open the file in read mode
            contents = file.readlines()
        
        # If the file is getting long, trim it. Doing 20 lines max for now to avoid huge files.
        if len(contents) > 30:
            contents = contents[-20:]  # Keep the last 20 lines

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
    
    # Attempt to connect to the Kobold CPP api and shutdown the bot if it's not up
    try: 
        api_check = requests.get(api_model)
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
    await client.tree.sync()
   
@client.event
async def on_message(message):
    
    # Check to see the bot should reply
    if should_bot_reply(message) == True:
        character = get_character_card()
        
        user_input = message.content.replace("<@1080950961268342874>","")
        user_input = user_input.strip()

        # Create the JSON prompt to use
        # history = read_context(str(message.author.name))
        # print(history)
        data = await create_prompt(message, str(message.author.name), character)
        
        # Add request to a queue to process
        queue_item = [data, message]
        queue_to_process.put_nowait(queue_item)

# Slash command to update the bot's personality
personality = app_commands.Group(name="personality", description="View or change the bot's personality.")

@personality.command(name="view", description="View the bot's personality profile.")
async def view_personality(interaction):
    # Display current personality.
    await interaction.response.send_message("The bot's current personality: **" + bot_persona + "**.")
    
@personality.command(name="set", description="Change the bot's personality.")
@app_commands.describe(persona="Describe the bot's new personality.")
async def edit_personality(interaction, persona: str):
    global bot_persona
            
    # Update the global variable
    old_personality = bot_persona
    bot_persona = persona
        
    # Display new personality, so we know where we're at
    await interaction.response.send_message("Bot's personality has been updated from \"" + old_personality + "\" to \"" + bot_persona + "\".")

@personality.command(name="reset", description="Reset the bot's personality to the default.")
async def reset_personality(interaction):
    global bot_persona
            
    # Update the global variable
    old_personality = bot_persona
    bot_persona = "coffee-loving, sarcastic friend with a dry sense of humor"
        
    # Display new personality, so we know where we're at
    await interaction.response.send_message("Bot's personality has been updated from \"" + old_personality + "\" to \"" + bot_persona + "\".")

# Slash commands to update the conversation history    
history = app_commands.Group(name="conversation-history", description="View or change the bot's personality.")

@history.command(name="reset", description="Reset your conversation history with the bot.")
async def reset_history(interaction):
    
    # Get the user who started the interaction and find their file.
    author = str(interaction.user.name)
    file_name = "context\\" + author + ".txt"

    # Attempt to remove the file and let the user know what happened.
    try:
        os.remove(file_name)
        await interaction.response.send_message("Your conversation history was deleted.")
    except FileNotFoundError:
         await interaction.response.send_message("There was no history to delete.")
    except PermissionError:
        await interaction.response.send_message("Something has gone wrong. Let bot owner know.")
    except Exception as e:
        await interaction.response.send_message("Something has gone wrong. Let bot owner know.")

@history.command(name="view", description=" View the last 20 lines of your conversation history.")
async def view_history(interaction):
    # Get the user who started the interaction and find their file.
    author = str(interaction.user.name)
    file_name = "context\\" + author + ".txt"
    
    try:
        with open(file_name, "r", encoding="utf-8") as file:  # Open the file in read mode
            contents = file.readlines()
            contents = contents[-20:]
            history_string = ''.join(contents)
            await interaction.response.send_message(history_string)
    except FileNotFoundError:
        await interaction.response.send_message("You have no history to display.")
    except Exception as e:
        await interaction.response.send_message("Something has gone wrong. Let bot owner know.")
    
    
# client.run('API_KEY')
client.run('MTA4MDk1MDk2MTI2ODM0Mjg3NA.G1iru4.KAO3foK7Wa5a_r76O4EHv6MkgZNq_vdiWV9Y70')
