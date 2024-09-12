import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a message to the user."""
    # Log the error with additional context
    log_error(update, context)

    # Notify the user that an error occurred
    update.message.reply_text(
        "An unexpected error occurred. Please try again or contact support if the issue persists."
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
            "It looks like you uploaded a non-image file. Please upload a valid photo (JPG/PNG format)."
        )
    else:
        update.message.reply_text(
            "Unsupported file type. Please upload a JPG image for your receipt."
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
        "Please upload a valid photo (JPG format) for your receipt."
    )


def notify_payment_feature_coming(update: Update) -> None:
    """Notifies the user that the proof of payment feature is coming soon."""
    update.message.reply_text(
        "This functionality is coming soon!", reply_markup=ReplyKeyboardRemove()
    )


def notify_invalid_option(update: Update) -> None:
    """Notifies the user that the input is not a valid option."""
    update.message.reply_text("I didn't understand that. Please select a valid option.")
