from dotenv import load_dotenv

load_dotenv()
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
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


def start(update: Update, context: CallbackContext) -> None:
    """Sends a greeting and provides options to the user."""
    welcome_msg = (
        "Hi, welcome to the Nepal Finance Bot!\n\n"
        "📂 *Directory:*\n"
        "/end - End the conversation at any time\n\n"
        "Please select one of the options below:\n\n"
        "📝 **Submit a Claim**\n"
        "🔍 **Check Claim Status**\n"
        "📸 **Submit Proof of Payment**\n"
    )
    update.message.reply_text(
        welcome_msg, reply_markup=get_main_menu_keyboard(3, 2), parse_mode="Markdown"
    )


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

    if context.user_data.get("waiting_for_description"):
        handle_description_input(update, context, user_response)
        return

    if context.user_data.get("waiting_for_receipt") or context.user_data.get(
        "waiting_for_payment_proof_receipt"
    ):
        # If waiting for an image but the user sends text, treat it as a non-image submission
        throw_text_error(update, context)
        return

    if context.user_data.get("waiting_for_payment_proof_name"):
        handle_payment_proof_name_input(update, context, user_response)
        return

    # Handle the main menu options
    if user_response == "Submit a Claim":
        initiate_claim_submission(update, context)
    elif user_response == "Check Claim Status":
        initiate_claim_status_check(update, context)
    elif user_response == "Submit Proof of Payment":
        initiate_payment_proof_submission(update, context)
    else:
        notify_invalid_option(update)


def end_conversation(update: Update, context: CallbackContext) -> None:
    """
    Handler to end the conversation.
    """
    context.user_data.clear()
    update.message.reply_text(
        "👋 Thanks for chatting! Feel free to choose an option below to continue whenever you're ready.",
        reply_markup=get_main_menu_keyboard(3, 2),
    )


def main() -> None:
    """
    Main function to start the bot.
    """
    # Fetch the bot token from environment variables for security
    updater = Updater(token=get_bot_api_key("BOTAPI_KEY"), use_context=True)
    dispatcher = updater.dispatcher

    # Command Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("end", end_conversation))

    # Message Handlers
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_response)
    )
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))
    dispatcher.add_handler(MessageHandler(Filters.document, non_image_handler))

    # unrecognisable commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

    # Error Handler
    dispatcher.add_error_handler(error_handler)

    # Start polling to run the bot
    updater.start_polling()

    # Keep the bot running until interrupted
    updater.idle()


if __name__ == "__main__":
    main()
