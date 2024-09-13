import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)
from utils import get_main_menu_keyboard


def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a message to the user."""
    # Log the error with additional context
    log_error(update, context)

    # Notify the user that an error occurred
    update.message.reply_text(
        "An unexpected error occurred. Please try again. \
        If the issue persists, please contact me @jer_jerryyy",
        # Please add ur tele handles here so people can contact us
        parse_mode="Markdown",
    )


def log_error(update: Update, context: CallbackContext) -> None:
    """Logs errors with additional context for debugging."""
    # Get information about the update and the error
    error_message = f"Update '{update}' caused error '{context.error}'"

    # Log the error (for now, we'll just print it, but this can be adapted to log to a file or external service)
    print(error_message)


# external logging function for future extensibility
def log_to_file(error_message: str) -> None:
    """Writes the error message to a log file."""
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()}: {error_message}\n")


def handle_invalid_image(update: Update) -> None:
    """Handles the case where an invalid image is uploaded."""
    update.message.reply_text("Please upload a valid JPG image.")


def request_valid_image(update: Update) -> None:
    """Prompts the user to upload a valid photo if the message doesn't contain a photo."""
    update.message.reply_text(
        "Please upload a valid photo (JPG format) for your receipt."
    )


def throw_text_error(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Sorry, only images are allowed! ⚠️ Please upload an image of your receipt."
    )


def non_image_handler(update: Update, context: CallbackContext) -> None:
    """Handles cases where the user sends non-photo files like .ipynb or other documents."""
    if update.message.document:
        handle_non_image_file(update, context)
    else:
        request_valid_image(update)


def handle_non_image_file(update: Update, context: CallbackContext) -> None:
    """Handles the scenario where a user uploads a non-image file."""
    file_type = update.message.document.mime_type
    if is_valid_non_image_file(file_type):
        update.message.reply_text(
            "📝 *It looks like you uploaded a non-image file.*\n\n"
            "Please upload a valid photo in *JPG* or *PNG* format."
        )
    else:
        update.message.reply_text(
            "🚫 I'm Sorry, we currently do not support this file type*\n\n"
            "Please upload an image of your receipt in *JPG* format."
        )


def is_valid_non_image_file(file_type: str) -> bool:
    """Checks if the uploaded file type is a valid non-image file."""
    # Extendable for future file types that might be supported
    valid_file_types = [
        "application/pdf",
        "application/zip",
        "text/csv",
        "application/x-ipynb+json",
    ]
    return file_type in valid_file_types


def request_valid_image(update: Update) -> None:
    """Prompts the user to upload a valid image if no document is uploaded."""
    update.message.reply_text(
        "🖼️ *Oops! It looks like you uploaded a document instead.*\n\n"
        "Please make sure to upload a clear image of your receipt in *JPG format*."
    )


def notify_payment_feature_coming(update: Update) -> None:
    """Notifies the user that the proof of payment feature is coming soon."""
    update.message.reply_text(
        "🚧 This feature is coming soon. Stay tuned:)",
        reply_markup=get_main_menu_keyboard(3, 2),
        parse_mode="Markdown",
    )


def notify_invalid_option(update: Update) -> None:
    """Notifies the user that the input is not a valid option."""
    error_message = """*Oops! 😕 I didn’t quite get that.*

It looks like you entered an *invalid option* or *command*. Don’t worry, it happens!

👉 Press /start to return to the main menu and explore the chat functions."""
    update.message.reply_text(error_message, parse_mode="Markdown")


def unknown_command(update: Update, context: CallbackContext) -> None:
    """
    Handles unknown commands and sends an error message.
    """
    update.message.reply_text(
        "⚠️ Sorry, that is not a valid command!\n\nHere are the available commands:\n /start - Start a new chat!\n/end - Reset conversation!",
        parse_mode="Markdown",
    )
