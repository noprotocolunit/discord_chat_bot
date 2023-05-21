# Discord Chat Bot w/ Queue and API

NoPro's silly little bot! 

It answers questions by making an API call to a koboldcpp instance. That's it. That's all it does. And it can sort of queue up answering questions (without too much screaming on its part).

To run this bot:

1. Install Textgen UI (or create a python-friendly environment somehow, don't ask me how)
2. Download this repository ( `github clone https://github.com/noprotocolunit/discord_chat_bot` )
3. Open bot.py and at the very bottom replace API_KEY with your bot's API key
4. Install llama-cpp-python server (if you did textgen, you have most of the parts) ( `pip install llama-cpp-python[server]` )
5. Install Discord ( `pip install Discord` )
6. Run the bot with `python bot.py`

Good luck!
