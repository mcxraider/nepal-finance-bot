import os
from dotenv import load_dotenv
import logging
import uuid
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# import our utils functions
from utils import fetch_sheet, get_claim_status, export_claim, send_receipt_to_cloud


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.environ["BOTAPI_KEY"]


# Error handler
def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and notify the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        update.effective_message.reply_text(
            "An error occurred. Please try again later."
        )


# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    """Sends a greeting and asks what the user wants to do"""

    reply_keyboard = [
        ["Submit a Claim", "Check Claim Status", "Submit Proof of Payment"]
    ]

    markup = ReplyKeyboardMarkup(
        reply_keyboard,
        one_time_keyboard=True,
        input_field_placeholder="What would you like to do?",
    )

    update.message.reply_text("Hello! What would you like to do?", reply_markup=markup)


def handle_response(update: Update, context: CallbackContext) -> None:
    """Handles the user's response to the main menu options."""
    user_response = update.message.text

    # Check if we're waiting for a claim ID
    if context.user_data.get("waiting_for_claim_id"):
        claim_id = user_response

        # fetch the google sheet
        data = fetch_sheet()

        # obtain the status
        status = get_claim_status(data, claim_id)
        if status["error"]:
            update.message.reply_text(
                f"You need to enter a valid claim id. {status['status_msg']} is not a valid ID"
            )
        else:
            answer = status["status_msg"]

            if answer in ["Approved", "Rejected"]:
                update.message.reply_text(f"Claim ID: {claim_id} has been {answer}")
            else:
                update.message.reply_text(f"Claim ID: {claim_id} is still {answer}")

        context.user_data["waiting_for_claim_id"] = False
        return

    if context.user_data.get("waiting_for_department"):
        context.user_data["department"] = user_response

        context.user_data["waiting_for_department"] = False
        context.user_data["waiting_for_name"] = True
        update.message.reply_text("Please enter your name:")
        return

    if context.user_data.get("waiting_for_name"):
        context.user_data["name"] = user_response

        context.user_data["waiting_for_name"] = False
        context.user_data["waiting_for_category"] = True
        update.message.reply_text("What are you claiming for?")
        return

    if context.user_data.get("waiting_for_category"):
        context.user_data["category"] = user_response

        context.user_data["waiting_for_category"] = False
        context.user_data["waiting_for_amount"] = True
        update.message.reply_text("Please enter the amount to claim:")
        return

    if context.user_data.get("waiting_for_amount"):
        context.user_data["amount"] = user_response

        context.user_data["waiting_for_receipt"] = True
        update.message.reply_text("Please upload a picture of the receipt.")

        context.user_data["waiting_for_amount"] = False
        return

    if user_response == "Submit a Claim":
        # Set the flag to ask for department
        context.user_data["waiting_for_department"] = True
        update.message.reply_text("Please enter the department:")

    # If not waiting for claim ID, handle other responses
    elif user_response == "Check Claim Status":

        # Set the flag to indicate we're waiting for the claim ID
        context.user_data["waiting_for_claim_id"] = True
        update.message.reply_text(
            "Please enter your claim ID: (Testing: refer to excel sheet for Claim ID)",
            reply_markup=ReplyKeyboardRemove(),
        )

    elif user_response == "Submit Proof of Payment":
        update.message.reply_text(
            "This functionality is coming soon!", reply_markup=ReplyKeyboardRemove()
        )

    else:
        update.message.reply_text(
            "I didn't understand that. Please select a valid option."
        )


def image_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles the receipt image sent by the user.
    """
    if context.user_data.get("waiting_for_receipt"):
        # Check if the message contains a photo
        if update.message.photo:
            photo_file = update.message.photo[-1].get_file()
            image_uuid = str(uuid.uuid4())

            # TODO: this can be edited to give users better access
            receipt_path = f"../receipts/{image_uuid}.jpg"

            try:
                # send it directly to Google Drive without saving locally
                send_receipt_to_cloud(receipt_path, photo_file)

                update.message.reply_text(
                    "Receipt received! Thank you for submitting your claim."
                )

            except ValueError:
                # Handle the case where the file is not a JPG
                update.message.reply_text("Please upload a valid JPG image.")
        else:
            # If the message doesn't contain a photo, prompt the user to send one
            update.message.reply_text(
                "Please upload a photo (JPG format) for your receipt."
            )

        # Reset waiting flag
        context.user_data["waiting_for_receipt"] = False

        # store the UUID in user_data for reference later
        context.user_data["receipt_uuid"] = image_uuid

        # Send user a confirmation message
        department = context.user_data.get("department", "").capitalize()
        name = context.user_data.get("name", "").capitalize()
        category = context.user_data.get("category", "").capitalize()
        amount = context.user_data.get("amount", "").capitalize()
        receipt_id = context.user_data.get("receipt_uuid", "").capitalize()

        confirmation_message = (
            f"Here is the claim you are making:\n"
            f"Department: {department}\n"
            f"Name: {name}\n"
            f"Expense Category: {category}\n"
            f"Amount: {amount}\n"
            f"Receipt ID (Please keep this ID safe!): {receipt_id}\n"
        )

        update.message.reply_text(confirmation_message)
        
        # Since this is the final stage, can send user data to the excel sheet
        export_claim(department, name, category, amount, receipt_id)


def non_photo_handler(update: Update, context: CallbackContext) -> None:
    """Handles cases where the user sends non-photo files like .ipynb or other documents."""
    # Check if the document is not an image
    if update.message.document:
        update.message.reply_text(
            "It looks like you uploaded a non-image file. Please upload a valid photo (JPG format)."
        )
    else:
        update.message.reply_text(
            "Please upload a valid photo (JPG format) for your receipt."
        )


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
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_response)
    )

    # Add handler for receipt image (photo)
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))

    # Add a generic handler for other file/document types
    dispatcher.add_handler(MessageHandler(Filters.document, non_photo_handler))

    # Log all errors
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
