import os
import discord
import requests
import json
import asyncio
import httpx
from aiohttp import ClientSession
from discord.ext import commands
from discord import app_commands
from discord import Interaction

intents = discord.Intents.default()
intents.message_content = True
api_url = "http://localhost:5001/api/v1/"

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# Create our queues up here somewhere
# Stuff that needs to be sent to the API
queue_to_process = asyncio.Queue()

#Stuff that needs to be sent to the user (post API)
queue_to_send = asyncio.Queue()

bot_name = "Night"
bot_persona = "dry-humored, coffee-loving, sarcastic AI sidekick"
bot_gender = "male"
bot_text_sample = "Night: Hello, what do you want?"


# Create a character card that will be added to the prompt sent to the LLM.
def get_character_card():

    # Your name is <name>.
    character_card = "Your name is " + bot_name + ". "
    
    # Your name is <name>. You are a <persona> with human-equivalent emotions and opinions.
    character_card = character_card + "You are a " + bot_persona + " with human-equivalent emotions and opinions. "
    
    # Your name is <name>. You are a <persona> with human-equivalent emotions and opinions. Your gender is <gender>. 
    character_card = character_card + "Your gender is " + bot_gender + ". "

    return character_card
        
def create_prompt(message, author, character):
    user_input = message.content.replace("<@1080950961268342874>","")
    user_input = user_input.strip()
    add_to_context(user_input, author)
    text = character + author + ": " + user_input + "\nNight: "

    data ={}
    data['n'] = 1
    data['max_context_length'] = 512
    data['max_length'] = 100
    data['prompt'] = text
    data['stop_sequence'] = [author+":", "Night:", "Day:", "\n\n"]
    data['rep_pen'] = 1.1
    data['temperature'] = 0.72
    data['top_p'] = 0.73
    data['top_k'] = 40
    data['sampler_order'] = [5, 0, 2, 6, 3, 4, 1] 
    
    prompt = json.dumps(data)
    return prompt
  
 
async def clean_reply(data, author):
        message = json.loads(data)
        dirty_message = str(message['results'][0]['text'])
        clean_message = dirty_message.replace(author + ":","")
        clean_message = clean_message.replace("\n\nNight:", "")
        add_to_context (clean_message, "Night")
        return clean_message
 
def add_to_context(data, author):
    with open('context.txt', 'a', encoding="utf-8") as context:
        context.write(author + ": " + data + "\n")
        context.close()
        

def read_context():
    return context
    
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
        print("Making API call.")
        async with ClientSession() as session:
            async with session.post(api_url + "generate", data=data) as response:
                response = await response.read()
                queue_item = [response, content[1]]  # content[1] is the message
                queue_to_send.put_nowait(queue_item)
                queue_to_process.task_done()
 
async def send_queue():
    while True:
        reply = await queue_to_send.get()
        answer = await clean_reply(reply[0], str(reply[1].author))
        await reply[1].channel.send(answer, reference=reply[1])   
        queue_to_send.task_done()

@client.event
async def on_ready():
    # Let owner known in the console that the bot is now running!
    print(f'NightBot is up and running.')
    
    # Attempt to connect to the Kobold CPP api and shutdown the bot if it's not up
    try: 
        api_check = requests.get(api_url + "model")
    except requests.exceptions.RequestException as e:
        print(f'LLM KoboldCPP api is not currently up. Shutting down the bot.')
        await client.close()
    
    #If we got there, then the API is up and here is the status of the model.
    print(api_check)
    
    asyncio.create_task(process_queue())
    asyncio.create_task(send_queue()) 
    
    await tree.sync()
 
@client.event
async def on_message(message):
    
    # Check to see the bot should reply
    if should_bot_reply(message) == True:
        character = get_character_card()
        
        # Create the JSON prompt to use
        data = create_prompt(message, str(message.author), character)
        
        # Add request to a queue to process
        queue_item = [data, message]
        queue_to_process.put_nowait(queue_item)

# Slash command to update the bot's personality     
@tree.command(name="personality", description="Adjust the bot's personality with this command.")
@app_commands.describe(persona="Describe the bot's new personality.")
async def personality(interaction, persona: str):

    global bot_persona
        
    # Update the global variable
    old_personality = bot_persona
    bot_persona = persona
    
    # Display new personality, so we know where we're at
    await interaction.response.send_message("Bot's personality has been updated from " + old_personality + " to " + bot_persona)
    
    
client.run('API_KEY')
