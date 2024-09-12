import uuid
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CallbackContext,
)

from drive_connector import *
from error_handling import *


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Generates the main menu reply keyboard for the user"""
    reply_keyboard = [
        ["Submit a Claim", "Check Claim Status", "Submit Proof of Payment"]
    ]

    return ReplyKeyboardMarkup(
        reply_keyboard,
        one_time_keyboard=True,
        input_field_placeholder="Select one of the options below",
    )


# Helper function to generate a UUID for the image
def generate_uuid() -> str:
    """Generates a unique UUID for the receipt image."""
    return str(uuid.uuid4())


def send_claim_confirmation(update: Update, context: CallbackContext) -> None:
    """Sends a confirmation message with the claim summary."""
    department = context.user_data.get("department", "").capitalize()
    name = context.user_data.get("name", "").capitalize()
    category = context.user_data.get("category", "").capitalize()
    amount = context.user_data.get("amount", "").capitalize()
    receipt_id = context.user_data.get("receipt_uuid", "").capitalize()

    # ensure the amount is formatted correctly
    if "$" not in amount:
        amount = "$" + amount

    confirmation_message = (
        "🧾 *Your Claim Summary* 🧾\n"
        "=============================\n"
        f"📌 *Department*: {department}\n"
        f"👤 *Name*: {name}\n"
        f"💼 *Expense Category*: {category}\n"
        f"💰 *Amount*: {amount}\n"
        "-----------------------------\n"
        f"🆔 *Claim ID*: `{receipt_id}`\n(Please *copy* this ID and keep it!)\n"
        "=============================\n"
    )

    update.message.reply_text(confirmation_message, parse_mode="Markdown")


def export_claim_details(context: CallbackContext) -> None:
    """Exports the claim details to Google Sheets."""
    department = context.user_data.get("department", "").capitalize()
    name = context.user_data.get("name", "").capitalize()
    category = context.user_data.get("category", "").capitalize()
    amount = context.user_data.get("amount", "").capitalize()
    receipt_id = context.user_data.get("receipt_uuid", "").capitalize()

    export_claim(department, name, category, amount, receipt_id)


def handle_claim_status_check(
    update: Update, context: CallbackContext, claim_id: str
) -> None:
    """Fetches claim status based on the claim ID provided by the user."""
    data = fetch_sheet()
    status = get_claim_status(data, claim_id)

    if status["error"]:
        update.message.reply_text(
            f"Invalid claim ID. {status['status_msg']} is not valid."
        )
    else:
        answer = status["status_msg"]
        if answer in ["Approved", "Rejected"]:
            update.message.reply_text(f"Claim ID: {claim_id} has been {answer}")
        # if status pending
        else:
            update.message.reply_text(f"Claim ID: {claim_id} is still {answer}")

    context.user_data["waiting_for_claim_id"] = False


def handle_department_input(
    update: Update, context: CallbackContext, department: str
) -> None:
    """Handles user input for the department during claim submission."""
    context.user_data["department"] = department
    context.user_data["waiting_for_department"] = False
    context.user_data["waiting_for_name"] = True
    update.message.reply_text("Please enter your name:")


def handle_name_input(update: Update, context: CallbackContext, name: str) -> None:
    """Handles user input for the name during claim submission."""
    context.user_data["name"] = name
    context.user_data["waiting_for_name"] = False
    context.user_data["waiting_for_category"] = True
    update.message.reply_text("What are you claiming for?")


def handle_category_input(
    update: Update, context: CallbackContext, category: str
) -> None:
    """Handles user input for the category during claim submission."""
    context.user_data["category"] = category
    context.user_data["waiting_for_category"] = False
    context.user_data["waiting_for_amount"] = True
    update.message.reply_text("Please enter the amount to claim:")


def handle_amount_input(update: Update, context: CallbackContext, amount: str) -> None:
    """Handles user input for the amount during claim submission."""
    context.user_data["amount"] = amount
    context.user_data["waiting_for_receipt"] = True
    update.message.reply_text(
        "Please upload a picture of the receipt.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["waiting_for_amount"] = False


def initiate_claim_submission(update: Update, context: CallbackContext) -> None:
    """Starts the claim submission process by asking for the department."""
    context.user_data["waiting_for_department"] = True
    update.message.reply_text("Please enter the department:")


def initiate_claim_status_check(update: Update, context: CallbackContext) -> None:
    """Starts the claim status check process by asking for the claim ID."""
    context.user_data["waiting_for_claim_id"] = True
    update.message.reply_text(
        "Please enter your claim ID:", reply_markup=ReplyKeyboardRemove()
    )


def handle_receipt_submission(update: Update, context: CallbackContext) -> None:
    """Handles the logic when a receipt is submitted by the user."""
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        context.user_data["image"] = photo_file

        image_uuid = generate_uuid()
        receipt_path = f"{image_uuid}"

        try:
            # Send the receipt to Google Drive
            send_receipt_to_cloud(receipt_path, photo_file)
            update.message.reply_text(
                "Receipt received! Thank you for submitting your claim."
            )

            # Store the UUID for reference and send confirmation
            context.user_data["receipt_uuid"] = receipt_path
            send_claim_confirmation(update, context)

            # Export claim details to Google Sheets
            export_claim_details(context)
        except ValueError:
            handle_invalid_image(update)
    else:
        # If no photo is provided, ask for a valid photo
        request_valid_image(update)
