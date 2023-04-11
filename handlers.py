from functools import wraps
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
import ftransc.core as ft
from config import menu_options
import config
import os
import yaml
import json
from types import SimpleNamespace
from collections import Counter


# create SECRET_KEYS singleton
SECRET_KEYS_PATH = "secret_keys.yaml"
if not os.path.exists(SECRET_KEYS_PATH):
    assert False, f"can't find {SECRET_KEYS_PATH}"
with open(SECRET_KEYS_PATH, "r") as f:
    SECRET_KEYS = SimpleNamespace(**yaml.safe_load(f))
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = SECRET_KEYS.GOOGLE_APPLICATION_CREDENTIALS
from google_api import synthesize_text, translate_text, upload_file, transcribe_voice


# create users history singleton
USERS_HIST_PATH = "history.json"
if not os.path.exists(USERS_HIST_PATH):
    USERS_HIST = dict()
else:
    with open(USERS_HIST_PATH, "r") as f:
        USERS_HIST = json.load(f)


def dump_user_hist():
    with open(USERS_HIST_PATH, "w") as f:
        json.dump(USERS_HIST, f)


def add_user(username):
    if username not in USERS_HIST:
        USERS_HIST[username] = list()


def add_word(username, word):
    USERS_HIST[username].append(word)
    dump_user_hist()


def get_top_words(username):
    c = Counter(USERS_HIST[username]).most_common(5)
    return [i[0] for i in c]


def send_typing_action(func):
    """
    Sends typing action while processing func command
    """

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


@send_typing_action
def start(update, context):
    """
    Send a message when the command /start is issued
    """
    status = check_id(update)
    add_user(update.message.chat.username)
    if status:
        first_name = update.message.chat.first_name
        opening_line = f"""Hi {first_name}! \nLet's start learning English together :)"""
        update.message.reply_text(opening_line)
        show_menu(update, context)


def show_menu(update, context):
    """
    Show menu buttons
    """
    keyboard = [
        [InlineKeyboardButton(menu_options['1']['option'], callback_data='1')],
        [InlineKeyboardButton(menu_options['2']['option'], callback_data='2')],
        [InlineKeyboardButton(menu_options['3']['option'], callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Would you like to learn... (click option below)', reply_markup=reply_markup)


def menu_option(update, context):
    """
    Send follow-up message after menu option is selected
    """
    query = update.callback_query
    if query.data == '3':
        top_words = get_top_words(query.from_user.username)
        s = "Top words:\n"
        for w in top_words:
            s += f"<b>{w}</b>\n"
        query.message.reply_text(s, parse_mode=ParseMode.HTML)
    else:
        context.chat_data['option'] = [query.data]
        query.edit_message_text(text=menu_options[query.data]['reply'])
        query.answer()


@send_typing_action
def help(update, context):
    """
    Send a message when the command /help is issued
    """
    status = check_id(update)
    if status:
        update.message.reply_text('Say hi or type /start to start chatting')


def send_audio(update, context, filename):
    """
    Send an audio message
    """
    if 'message_id' in context.user_data.keys():
        try:
            # delete previous audio message, if any, so that Telegram's auto-play does not drive user crazy
            context.bot.delete_message(chat_id=context.user_data['chat_id'][0], message_id=context.user_data['message_id'][0])
        except Exception as e:
            print(e)
    message = context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=open(filename, 'rb'))
    context.user_data['chat_id'] = [message.chat.id]
    context.user_data['message_id'] = [message.message_id]


@send_typing_action
def message_reply(update, context):
    """
    Response to normal messages
    """
    status = check_id(update)
    if status:
        filename = 'pronunciation.mp3'
        if 'option' in context.chat_data.keys():
            if context.chat_data['option'][0]=='1':  # option 1 selected in previous step        
                synthesize_text(update.message.text, filename)
                add_word(update.message.chat.username, update.message.text)
                send_audio(update, context, filename)
                followup_line = f"""Hope that helps :) \nIs there anything else you would like to do?"""
                update.message.reply_text(followup_line)
                show_menu(update, context)
                context.chat_data['filename'] = [filename]
                context.chat_data['option'] = ['']

            elif context.chat_data['option'][0]=='2': # option 2 selected in previous step 
                translated_text = translate_text(update.message.text)
                synthesize_text(translated_text, filename)
                add_word(update.message.chat.username, update.message.text)
                send_audio(update, context, filename)
                followup_line = f"""Please repeat after me and send your recorded voice over the chat to check if you've pronounce it correctly"""
                update.message.reply_text(followup_line)
                context.chat_data['translated_text'] = [translated_text]
                context.chat_data['text'] = [update.message.text]
                context.chat_data['filename'] = [filename]
                context.chat_data['option'] = ['']

            else:
                followup_line = f"""Would you like to do the following?"""
                update.message.reply_text(followup_line)
                show_menu(update, context)
        else:
            if update.message.text.lower() in ['hi', 'hello', 'yo', 'good morning', 'good afternoon', 'good evening']:
                start(update, context)
            else:
                update.message.reply_text("Sorry, I'm a young bot so I've trouble understanding you. \n Would you like to do the following?")
                show_menu(update, context)


@send_typing_action
def voice_check(update, context):
    """
    Check user's pronunciations against correct answer
    """
    status = check_id(update)
    if status:
        # Fetch voice message
        voice = context.bot.getFile(update.message.voice.file_id)

        # Transcode the voice message from audio/x-opus+ogg to audio/x-wav
        filename = 'pronunciation' + '_2.ogg'
        ft.transcode(voice.download(filename), 'wav')

        new_filename = filename[:-3] + 'wav'
        upload_file(new_filename, SECRET_KEYS.BUCKET_NAME)
        response_text = transcribe_voice(new_filename, SECRET_KEYS.BUCKET_NAME)
        correct = context.chat_data['translated_text'][0].lower()
        response = response_text.lower()

        if response==correct:
            update.message.reply_text("That's correct! Good job!")
            update.message.reply_text("Is there anything else you would like to do?")
            show_menu(update, context)
            context.chat_data['option'] = ['']
        else:
            update.message.reply_text(f"Oops, you said c{response}</b>! That's not correct. Please try saying <b>{context.chat_data['text'][0]}</b> in <b>{config.language_code.split('-')[1]}</b> again", parse_mode=ParseMode.HTML)
            translated_voice_filename = context.chat_data['filename'][0]
            send_audio(update, context, translated_voice_filename)


def check_id(update):
    """
    Check sender's ID is allowed
    """
    id = int(update.message.from_user.id)
    verification = True if (id==SECRET_KEYS.TELEGRAM_ID or SECRET_KEYS.TELEGRAM_ID is None) else False
    if verification is False:
        update.message.reply_text("Oops! I don't really know you so I cannot talk to you. \n\nSorry about that!")
    return verification