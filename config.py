tts_model_name = "en-GB-Neural2-C"
language_code = "en-GB"
# Options for the Telegram menu buttons 
menu_options = {
        '1': {
                'option':"How to pronounce EN word(s)",
                'reply': "Ok, let's hear the pronunciation of EN word(s). \n\nEnter the EN word(s) into the chat box"
        },
        '2': {
                'option':"How to say (RU) in EN",
                'reply':"Ok, let's learn how to say (RU) in EN. \n\nWhat is/are the RU word(s)?"
        },
        '3': {
                'option':"Top-5 your words",
                'reply':"Here is your top-5 words from history"
        },
        '4': {
                'option':"Hardest words to pronounce",
                'reply':"Here are the hardest words"
        }

}
# hardest words to pronounce
hardest_words = [
    "anemone",
    "squirrel",
    "rural",
    "synecdoche",
    "colonel",
    "phenomenon"
]