import os
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# import our functions
from drive_connector import *
from error_handling import *
from utils import *

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.environ["BOTAPI_KEY"]


# Refactored start function
def start(update: Update, context: CallbackContext) -> None:
    """Sends a greeting and asks what the user wants to do"""
    
    # Modular function to get the reply keyboard
    reply_markup = get_main_menu_keyboard()

    update.message.reply_text("Hello! What would you like to do?", reply_markup=reply_markup)


def handle_response(update: Update, context: CallbackContext) -> None:
    """Handles the user's response to the main menu options."""
    user_response = update.message.text

    if context.user_data.get("waiting_for_claim_id"):
        handle_claim_status_check(update, context, user_response)
        return

    if context.user_data.get("waiting_for_department"):
        handle_department_input(update, context, user_response)
        return

    if context.user_data.get("waiting_for_name"):
        handle_name_input(update, context, user_response)
        return

    if context.user_data.get("waiting_for_category"):
        handle_category_input(update, context, user_response)
        return

    if context.user_data.get("waiting_for_amount"):
        handle_amount_input(update, context, user_response)
        return

    # Handle the main menu options
    if user_response == "Submit a Claim":
        initiate_claim_submission(update, context)
    elif user_response == "Check Claim Status":
        initiate_claim_status_check(update, context)
    elif user_response == "Submit Proof of Payment":
        # TODO: Create submit proof functionality
        notify_payment_feature_coming(update)
    else:
        notify_invalid_option(update)


def image_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles the receipt image sent by the user.
    """
    if context.user_data.get("waiting_for_receipt"):
        handle_receipt_submission(update, context)
        context.user_data["waiting_for_receipt"] = False  


def main() -> None:
    """
    Main function to start the bot.
    """

    # Create the Updater and pass it your bot's token
    updater = Updater(token=BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add the start command handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Add a generic message handler for non-command messages
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_response))

    # Add handler for receipt image (photo)
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))

    # Add a generic handler for other file/document types
    dispatcher.add_handler(MessageHandler(Filters.document, non_image_handler))

    # Log all errors
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
