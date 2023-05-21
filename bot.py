import os
import discord
import requests
import json
import asyncio
import httpx
import random
from aiohttp import ClientSession
from discord.ext import commands
from discord import app_commands
from discord import Interaction

intents = discord.Intents.all()
intents.message_content = True
api_url = "http://localhost:8000/v1/"

client = commands.Bot(command_prefix='$', intents=intents)

# Create our queues up here somewhere
# Stuff that needs to be sent to the API
queue_to_process = asyncio.Queue()

#Stuff that needs to be sent to the user (post API)
queue_to_send = asyncio.Queue()

bot_name = "Night"
bot_persona = "coffee-loving, sarcastic friend with a dry sense of humor"
bot_gender = "male"
bot_text_sample = "Night: Hello, what do you want?"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Create a character card that will be added to the prompt sent to the LLM.
def get_character_card():

    # Your name is <name>.
    character_card = "Your name is " + bot_name + ". "
    
    # Your name is <name>. You are a <persona> and have emotions and opinions.
    character_card = character_card + "You are a " + bot_persona + " and have emotions and opinions. "
    
    # Your name is <name>. You are a <persona> with human-equivalent emotions and opinions. Your gender is <gender>. 
    # character_card = character_card + "Your gender is " + bot_gender + ". "

    return character_card
        
def create_prompt(message, author, character):

    # Take the provided message and strip out @NightBot
    user_input = message.content.replace("<@1080950961268342874>","")
    
    # Remove any spaces before and after the input.
    user_input = user_input.strip()
    
    # Create the prompt that will be sent in the prompt field.
    text = character + author + ": " + user_input + "\nNight: "

    # Make me a JSON file
    data = {
        "prompt": text,
        "stop": [author+":", "Night:", "\n\n"],
        "max_tokens": 100,
        "user": author,
        "temperature": 0.72,
        "top_p": 0.73,
        "top_k": 0,
        "repeat_penalty": 1.08,
        "n": 1,
        "seed": 0,
        "mirostat_mode": 2,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.2
}
    
    # Turn the thing into a JSON string and return it
    prompt = json.dumps(data)
    return prompt
  
async def clean_reply(data, author):
        message = json.loads(data)
        dirty_message = str(message['choices'][0]['text'])
        clean_message = dirty_message.replace(author + ":","")
        clean_message = clean_message.replace("\n\nNight:", "")
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
        print("Sending" + data)
        global headers
        async with ClientSession() as session:
            async with session.post(api_url + "completions", headers=headers, data=data) as response:
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

@client.event
async def on_ready():
    # Let owner known in the console that the bot is now running!
    print(f'NightBot is up and running.')
    
    # Attempt to connect to the Kobold CPP api and shutdown the bot if it's not up
    try: 
        api_check = requests.get(api_url + "models")
    except requests.exceptions.RequestException as e:
        print(f'LLM KoboldCPP api is not currently up. Shutting down the bot.')
        await client.close()
    
    #If we got there, then the API is up and here is the status of the model.
    print(api_check)
    
    #AsynchIO Tasks
    asyncio.create_task(process_queue())
    asyncio.create_task(send_queue())
    
    # Sync current slash commands (commented out unless we have new commands)
    client.tree.add_command(personality)
    await client.tree.sync()
   
@client.event
async def on_message(message):
    
    # Check to see the bot should reply
    if should_bot_reply(message) == True:
        character = get_character_card()
        
        # Create the JSON prompt to use
        data = create_prompt(message, str(message.author.name), character)
        
        # Add request to a queue to process
        queue_item = [data, message]
        queue_to_process.put_nowait(queue_item)

# Slash command to update the bot's personality
personality = app_commands.Group(name="personality", description="View or change the bot's personality.")

@personality.command(name="view", description="View the bot's personality profile.")
async def view_personality(interaction):
    # Display current personality.
    await interaction.response.send_message("The bot's current personality: **" + bot_persona + "**.")
    
@personality.command(name="edit", description="Change the bot's personality.")
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
    
client.run('API_KEY')

