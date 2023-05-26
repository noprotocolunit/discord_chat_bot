def get_character_card():

    # Your name is <name>.
    character_card = "Your name is " + bot_name + ". "
    
    # Your name is <name>. You are a <persona>.
    character_card = character_card + "You are a " + bot_persona + ". " + bot_censorship + bot_text_sample
    
    # Your name is <name>. You are a <persona> with human-equivalent emotions and opinions. Your gender is <gender>. 
    # character_card = character_card + "Your gender is " + bot_gender + ". "

    return character_card