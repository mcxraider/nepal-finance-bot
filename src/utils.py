import uuid
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackContext,
)
import re

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


def generate_uuid() -> str:
    """Generates a unique UUID for the receipt image."""
    return str(uuid.uuid4())


def get_department_keyboard() -> InlineKeyboardMarkup:
    """Creates an inline keyboard for department selection."""
    keyboard = [
        [
            InlineKeyboardButton("Logistics", callback_data="Logistics"),
            InlineKeyboardButton("Finance", callback_data="Finance"),
        ],
        [
            InlineKeyboardButton("First Aid", callback_data="First Aid"),
            InlineKeyboardButton("Blog", callback_data="Blog"),
        ],
        [
            InlineKeyboardButton("Publicity", callback_data="Publicity"),
            InlineKeyboardButton("Flights & Accoms", callback_data="Flights & Accoms"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_department_keyboard() -> ReplyKeyboardMarkup:
    """Creates a reply keyboard for department selection."""
    keyboard = [
        ["Logistics", "Finance"],
        ["First Aid", "Blog"],
        ["Publicity", "Flights & Accoms"],
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def handle_department_input(
    update: Update, context: CallbackContext, user_response: str
) -> None:
    """Handles user input for the department during claim submission."""

    # Define the valid departments
    valid_departments = [
        "Logistics",
        "Finance",
        "First Aid",
        "Blog",
        "Publicity",
        "Flights & Accoms",
    ]

    # If user hasn't selected yet, show the keyboard
    if user_response not in valid_departments:
        reply_markup = get_department_keyboard()
        update.message.reply_text(
            "Please choose your department:", reply_markup=reply_markup
        )
        context.user_data["waiting_for_department"] = True
    else:
        # If valid department is selected, store and proceed to the next step
        context.user_data["department"] = user_response
        context.user_data["waiting_for_department"] = False
        context.user_data["waiting_for_name"] = True
        update.message.reply_text(
            f"Department Selected: {user_response}", reply_markup=ReplyKeyboardRemove()
        )
        update.message.reply_text(
            "Please enter your name:", reply_markup=ReplyKeyboardRemove()
        )


def handle_name_input(update: Update, context: CallbackContext, name: str) -> None:
    """Handles user input for the name during claim submission."""
    context.user_data["name"] = name
    context.user_data["waiting_for_name"] = False
    context.user_data["waiting_for_category"] = True
    update.message.reply_text(
        "What are you claiming for?", reply_markup=ReplyKeyboardRemove()
    )


def handle_category_input(
    update: Update, context: CallbackContext, category: str
) -> None:
    """Handles user input for the category during claim submission."""
    context.user_data["category"] = category
    context.user_data["waiting_for_category"] = False
    context.user_data["waiting_for_amount"] = True
    update.message.reply_text(
        "Please enter the amount to claim:", reply_markup=ReplyKeyboardRemove()
    )


def filter_valid_amount(amount: str) -> str:
    """Filters the input and keeps only valid amount format."""
    if "$" not in amount:
        amount = "$" + amount
    # Clean the users input amount so that it doesnt contain characters
    pattern = r"\$?\d+(\.\d{0,2})?"
    match = re.search(pattern, amount)

    return match.group(0) if match else ""


def handle_amount_input(
    update: Update, context: CallbackContext, input_amount: str
) -> None:
    """Handles user input for the amount during claim submission."""
    # ensure the amount is formatted correctly
    amount = filter_valid_amount(input_amount)

    context.user_data["amount"] = amount
    context.user_data["waiting_for_description"] = True
    update.message.reply_text(
        f"Amount to claim: {amount}", reply_markup=ReplyKeyboardRemove()
    )
    update.message.reply_text(
        "Please provide a brief description of the claim you are making:",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data["waiting_for_amount"] = False


def handle_description_input(
    update: Update, context: CallbackContext, description: str
) -> None:
    """Handles user input for the description of what they are claiming for ."""

    context.user_data["description"] = description
    context.user_data["waiting_for_receipt"] = True
    update.message.reply_text(
        "Please upload a picture of the receipt.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["waiting_for_description"] = False


def initiate_claim_submission(update: Update, context: CallbackContext) -> None:
    """Initiates the claim submission process by showing department selection."""

    reply_markup = get_department_keyboard()
    update.message.reply_text(
        "Please choose your department:", reply_markup=reply_markup
    )

    # Set the flag to indicate that we are waiting for the department selection
    context.user_data["waiting_for_department"] = True


def initiate_claim_status_check(update: Update, context: CallbackContext) -> None:
    """Starts the claim status check process by asking for the claim ID."""
    context.user_data["waiting_for_claim_id"] = True
    update.message.reply_text(
        "Please enter your claim ID:", reply_markup=ReplyKeyboardRemove()
    )


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


def send_user_claim_confirmation(update: Update, context: CallbackContext) -> None:
    """Sends a confirmation message with the claim summary."""
    department = context.user_data.get("department", "").capitalize()
    name = context.user_data.get("name", "").capitalize()
    category = context.user_data.get("category", "").capitalize()
    amount = context.user_data.get("amount", "").capitalize()
    description = context.user_data.get("description", "").capitalize()
    receipt_id = context.user_data.get("receipt_uuid", "").capitalize()

    confirmation_message = (
        "🧾 *Your Claim Summary* 🧾\n"
        "=============================\n"
        f"📌 *Department*:             {department}\n"
        f"👤 *Name*:                        {name}\n"
        f"💼 *Expense Category*:  {category}\n"
        f"💰 *Amount*:                    {amount}\n"
        f"📝 *Description*:              {description}\n"
        "=============================\n"
        f"*Claim ID*: \n`{receipt_id}`\n"
        "_(Please copy this ID and keep it!)_\n"
        "=============================\n"
    )

    update.message.reply_text(confirmation_message, parse_mode="Markdown")


def handle_receipt_submission(update: Update, context: CallbackContext) -> None:
    """Handles the logic when a receipt is submitted by the user."""
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        context.user_data["image"] = photo_file
        receipt_path = f"{generate_uuid()}"

        try:
            # Send the receipt to Google Drive
            send_receipt_to_cloud(receipt_path, photo_file)

            # Store the UUID for reference and send confirmation
            context.user_data["receipt_uuid"] = receipt_path
            update.message.reply_text("Image submitted!")
            send_user_claim_confirmation(update, context)

            # Export claim details to Google Drive
            export_claim_details(context)
        except ValueError:
            handle_invalid_image(update)
    else:
        # If no photo is provided, ask for a valid photo
        request_valid_image(update)
