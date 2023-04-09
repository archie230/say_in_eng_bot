import logging
import handlers
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters


def main():
    """
    Main function to start the bot
    """
    # Create the Updater and pass it your bot's token.
    updater = Updater(handlers.SECRET_KEYS.BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", handlers.start))
    dp.add_handler(CallbackQueryHandler(handlers.menu_option))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, handlers.message_reply))

    # Attach voiemessage handler to dispatcher. Note the filter as we ovly want the voice mesages to be transcribed
    dp.add_handler(MessageHandler(Filters.voice, handlers.voice_check))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
