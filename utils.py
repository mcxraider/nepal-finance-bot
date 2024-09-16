import uuid
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from drive_connector import *
from error_handling import *


def create_reply_keyboard(
    options: list[str], rows: int, columns: int, placeholder: str = None
) -> ReplyKeyboardMarkup:
    """
    Generates a dynamic reply keyboard for the user based on the provided shape (rows and columns).
    """
    # Create the keyboard layout based on the given rows and columns
    keyboard_layout = [
        options[i : i + columns] for i in range(0, len(options), columns)
    ]

    return ReplyKeyboardMarkup(
        keyboard_layout,
        one_time_keyboard=True,
        input_field_placeholder=placeholder,
        selective=True,  # Ensures only the user sees the keyboard
    )


def get_main_menu_keyboard(rows: int, columns: int) -> ReplyKeyboardMarkup:
    """Generates the main menu reply keyboard for the user with custom rows and columns."""
    options = ["Submit a Claim", "Check Claim Status", "Submit Proof of Payment"]
    return create_reply_keyboard(
        options, rows, columns, placeholder="Select one of the options below"
    )


def get_department_keyboard(rows: int, columns: int) -> ReplyKeyboardMarkup:
    """Creates a dynamic reply keyboard for department selection."""
    options = [
        "Logistics",
        "Finance",
        "First Aid",
        "Blog",
        "Publicity",
        "Flights & Accoms",
    ]
    return create_reply_keyboard(
        options, rows, columns, placeholder="Select your department"
    )


def generate_uuid() -> str:
    """Generates a unique UUID for the receipt image."""
    return str(uuid.uuid4())[:-3]


def handle_department_input(
    update: Update, context: CallbackContext, user_response: str
) -> None:
    """Handles user input for the department during claim submission."""

    valid_departments = [
        "Logistics",
        "Flights & Accoms",
        "First Aid",
        "Finance",
        "Blog",
        "Publicity",
    ]

    # If user hasn't selected yet, show the keyboard
    if user_response not in valid_departments:
        reply_markup = get_department_keyboard(2, 3)
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


def filter_valid_amount(amount: str, pattern=r"\$?\d+(\.\d{0,2})?") -> str:
    """Filters the input and keeps only valid amount format."""
    if "$" not in amount:
        amount = "$" + amount
    # Clean the users input amount so that it doesn't contain characters
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

    reply_markup = get_department_keyboard(3, 2)
    update.message.reply_text(
        "Please choose your department:", reply_markup=reply_markup
    )

    # Set the flag to indicate that we are waiting for the department selection
    context.user_data["waiting_for_department"] = True


def initiate_claim_status_check(update: Update, context: CallbackContext) -> None:
    """Starts the claim status check process by asking for the claim ID."""
    context.user_data["waiting_for_claim_id"] = True
    update.message.reply_text(
        "Please enter the ID of your claim:", reply_markup=ReplyKeyboardRemove()
    )


def handle_invalid_claim_id(update: Update, context: CallbackContext, status):
    update.message.reply_text(
        f"⚠️ Oops! It seems like the claim ID '{status['status_msg']}' is invalid.\n\n"
        "Please double-check that you have the correct Claim ID and restart the claim checking process!\n"
        "To restart the conversation: /start\n\n"
        "If the Claim ID is invalid after a few attempts, please contact any of the members in the finance team!"
    )


def handle_claim_status_check(
    update: Update, context: CallbackContext, claim_id: str
) -> None:
    """Fetches claim status based on the claim ID provided by the user."""
    data = fetch_sheet()
    status = get_claim_status(data, claim_id)

    if status["error"]:
        handle_invalid_claim_id(update, context, status)

    else:
        answer = status["status_msg"].lower()
        if answer in ["approved", "rejected"]:
            # Format the message for approved or rejected claims
            update.message.reply_text(
                f"✅ *Status Update* \n\nYour claim (ID: `{claim_id}`) has been *{answer}*.\n\nThank you for your patience!",
                reply_markup=get_main_menu_keyboard(3, 2),
                parse_mode="Markdown",
            )
        else:
            # Format the message for claims still in process
            update.message.reply_text(
                f"⌛ *Processing Update* \n\nThe Claim ID: `{claim_id}` is still being processed.\n\nPlease check back later for an update. We appreciate your understanding!",
                reply_markup=get_main_menu_keyboard(3, 2),
                parse_mode="Markdown",
            )

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

    update.message.reply_text(
        confirmation_message,
        reply_markup=get_main_menu_keyboard(3, 2),
        parse_mode="Markdown",
    )


def image_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles the receipt image sent by the user.
    """
    if context.user_data.get("waiting_for_receipt"):
        handle_receipt_submission(update, context)
        context.user_data["waiting_for_receipt"] = False

    elif context.user_data.get("waiting_for_payment_proof_receipt"):
        handle_payment_proof_submission(update, context)
        context.user_data["waiting_for_payment_proof_receipt"] = False


def handle_receipt_submission(update: Update, context: CallbackContext) -> None:
    """Handles the logic when a receipt is submitted by the user."""
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        context.user_data["image"] = photo_file
        receipt_path = f"{generate_uuid()}"

        try:
            # Send the receipt to Google Drive
            send_claim_receipt_to_cloud(receipt_path, photo_file)

            # Store the UUID for reference and send confirmation
            context.user_data["receipt_uuid"] = receipt_path
            update.message.reply_text("Image received!")
            send_user_claim_confirmation(update, context)

            # Export claim details to Google Drive
            export_claim_details(context)
        except ValueError:
            handle_invalid_image(update)
    else:
        # If no photo is provided, ask for a valid photo
        request_valid_image(update)


def initiate_payment_proof_submission(update: Update, context: CallbackContext) -> None:
    """Starts the payment proof submission process by asking for the persons name."""
    update.message.reply_text(
        "Please enter your name! (eg John_Doe)", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["waiting_for_payment_proof_name"] = True


def handle_payment_proof_name_input(
    update: Update, context: CallbackContext, name: str
) -> None:
    """Handles user input for the users name for the payment tracking."""

    context.user_data["name"] = name
    context.user_data["waiting_for_payment_proof_receipt"] = True
    update.message.reply_text(
        "Please upload a picture of your proof of payment!",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data["waiting_for_payment_proof_name"] = False


def send_user_payment_proof_confirmation(
    update: Update, context: CallbackContext
) -> None:
    """Sends a confirmation message with the submission summary."""
    name = context.user_data.get("name", "").capitalize()
    receipt_id = context.user_data.get("receipt_uuid", "").capitalize()

    confirmation_message = (
        "🧾 *Your Submission Summary* 🧾\n"
        "=============================\n"
        f"👤 *Name*:            {name}\n"
        "=============================\n"
        f"*Submission ID*: \n`{receipt_id}`\n"
        "_(Please copy this ID and keep it!)_\n"
        "=============================\n"
    )

    update.message.reply_text(
        confirmation_message,
        reply_markup=get_main_menu_keyboard(3, 2),
        parse_mode="Markdown",
    )


def handle_payment_proof_submission(update: Update, context: CallbackContext) -> None:
    """Handles the logic when a proof of payment is submitted by the user."""
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        context.user_data["image"] = photo_file
        name = context.user_data["name"]
        receipt_path = f"{name}_{generate_uuid()}"
        try:
            # Send the receipt to Google Drive
            send_payment_proof_to_cloud(receipt_path, photo_file)

            # Store the UUID for reference and send confirmation
            context.user_data["receipt_uuid"] = receipt_path
            update.message.reply_text("Image submitted!")
            send_user_payment_proof_confirmation(update, context)

        except ValueError:
            handle_invalid_image(update)
    else:
        # If no photo is provided, ask for a valid photo
        request_valid_image(update)


def payment_proof_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles the receipt image sent by the user.
    """
    if context.user_data.get("waiting_for_payment_proof_receipt"):
        handle_payment_proof_submission(update, context)
        context.user_data["waiting_for_payment_proof_receipt"] = False
