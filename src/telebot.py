import os
from dotenv import load_dotenv
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from fetch_sheet import fetch_sheet, get_claim_status
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.environ['botapi_key']  # Retrieves the bot token from .env file

# Define states for conversation flow
ASK_CLAIM_ID = 1

# Error handler
def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and notify the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        update.effective_message.reply_text('An error occurred. Please try again later.')


# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    """Sends a greeting and asks what the user wants to do"""
    
    reply_keyboard = [['Submit a Claim', 'Check Claim Status', 'Submit Proof of Payment']]

    markup = ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True, input_field_placeholder='What would you like to do?'
    )

    update.message.reply_text(
        "Hello! What would you like to do?",
        reply_markup=markup
    )
    
def handle_response(update: Update, context: CallbackContext) -> None:
    """Handles the user's response to the main menu options."""
    user_response = update.message.text

    # Check if we're waiting for a claim ID
    if context.user_data.get('waiting_for_claim_id'):
        claim_id = user_response
        
        # fetch the google sheet
        data = fetch_sheet()
        
        # obtain the status
        status = get_claim_status(data, claim_id)
        if status['error']:
            update.message.reply_text(f"You need to enter a valid claim id. {status['id']} is not a valid ID")
        else:
            answer = status['status_msg']
            
            if answer in ['Approved', 'Rejected']:
                update.message.reply_text(f"Claim ID: {claim_id} has been {answer}")
            else:
                update.message.reply_text(f"Claim ID: {claim_id} is still {answer}")
        
        # Reset the waiting flag
        context.user_data['waiting_for_claim_id'] = False
        return

    # If not waiting for claim ID, handle other responses
    if user_response == 'Check Claim Status':
        # Set the flag to indicate we're waiting for the claim ID
        context.user_data['waiting_for_claim_id'] = True
        update.message.reply_text("Please enter your claim ID:", reply_markup=ReplyKeyboardRemove())

    elif user_response == 'Submit a Claim':
        update.message.reply_text("This functionality is coming soon!", reply_markup=ReplyKeyboardRemove())

    elif user_response == 'Submit Proof of Payment':
        update.message.reply_text("This functionality is coming soon!", reply_markup=ReplyKeyboardRemove())

    else:
        update.message.reply_text("I didn't understand that. Please select a valid option.")


# # Response handler for different options
# def handle_response(update: Update, context: CallbackContext) -> int:
#     """Handles the user's response to the main menu options."""
#     user_response = update.message.text

#     if user_response == 'Check Claim Status':
#         update.message.reply_text("Please enter your claim ID:", reply_markup=ReplyKeyboardRemove())
        
#         claim_id = update.message.text
        
#         data = fetch_sheet()
#         status = get_claim_status(data, claim_id)
#         update.message.reply_text(f"The status of your claim: {status}")
#         return ConversationHandler.END  
    
#     elif user_response == 'Submit a Claim':
#         update.message.reply_text("This functionality is coming soon!", reply_markup=ReplyKeyboardRemove())
#         return ConversationHandler.END

#     elif user_response == 'Submit Proof of Payment':
#         update.message.reply_text("This functionality is coming soon!", reply_markup=ReplyKeyboardRemove())
#         return ConversationHandler.END
    
#     else:
#         update.message.reply_text("I didn't understand that. Please select a valid option.")
#         return ConversationHandler.END



# Main function to run the bot
def main() -> None:
    """Start the bot."""
    
    # Create the Updater and pass it your bot's token
    updater = Updater(token=BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add the start command handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Add a generic message handler for non-command messages
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_response))

    # Log all errors
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM, or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
