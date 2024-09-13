# TeleBot for Nepal Trip

A utility telegram bot for the STEER Nepal trip. Provides some admin features for the finance team.

## Table of Contents
- [TeleBot for Nepal Trip](#telebot-for-nepal-trip)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
- [Additional feature needed:](#additional-feature-needed)
  - [Prerequisites](#prerequisites)
  - [Setup Guide](#setup-guide)
    - [Google Sheets API Setup](#google-sheets-api-setup)
    - [Google Drive API Setup](#google-drive-api-setup)
  - [Installation](#installation)
  - [Bot Configuration](#bot-configuration)
  - [Running the Bot](#running-the-bot)
  - [File Structure](#file-structure)
  - [Contributing](#contributing)
    - [How to Contribute](#how-to-contribute)
    - [Linting](#linting)
    - [Working with python-telegram-bot](#working-with-python-telegram-bot)

## Features
- **Submit Claims**: Users can submit claims by entering the department, name, claim category, and amount, followed by uploading a receipt photo.
- **Check Claim Status**: Users can check the status of their claim by providing a claim ID.
- **Receipt Storage**: Receipts are uploaded to Google Drive, and the claim details are stored in a Google Sheet.

# Additional feature needed:
- **Submitting proof of payment**: Users can use this to submit proof that they have sent money to the account

## Prerequisites
Before setting up the bot, ensure you have the following:
1. **Python 3.8+** installed on your machine.
2. A **Telegram Bot Token**. You can create a new bot via [BotFather](https://core.telegram.org/bots#botfather).
3. **Google Cloud Project** with Google Sheets and Google Drive API enabled.
4. **Pip** for installing the required dependencies.

## Setup Guide

### Google Sheets API Setup
1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
   
2. **Enable the Google Sheets API**:
   - Navigate to the [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) and click **Enable**.
   
3. **Create OAuth Credentials**:
   - Go to the [Credentials page](https://console.cloud.google.com/apis/credentials).
   - Click on **Create Credentials** > **OAuth 2.0 Client IDs**.
   - Select **Desktop App** as the application type.
   - Download the credentials file (`credentials.json`) and save it in the root directory of the project.

4. **Create a Google Sheet**:
   - Create a new Google Sheet and note its ID (you can find this in the URL of the sheet).
   - Share the sheet with the email address generated in the `credentials.json` file (e.g., `your-project@your-project.iam.gserviceaccount.com`) and give it edit access.

### Google Drive API Setup
1. **Enable the Google Drive API**:
   - Go to the [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) and click **Enable**.
   
2. **Create a Google Drive Folder**:
   - Create a folder in your Google Drive to store the uploaded receipt images.
   - Note the folder ID from the URL (the part after `folders/` in the URL).
   
3. **Share the Folder**:
   - Share the folder with the email address from the `credentials.json` file, giving it edit permissions.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/nepal-finance.git
   cd nepal-finance
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Google API Dependencies**:
   Make sure you have the `credentials.json` file in the root directory, which you generated during the [Google API setup](#setup-guide).

## Bot Configuration

1. **Set Up Environment Variables**:
   Create a `.env` file in the root directory to store your bot token and other important configurations:
   ```bash
   BOT_TOKEN="your-telegram-bot-token"
   SAMPLE_SPREADSHEET_ID="your-google-sheet-id"
   DRIVE_FOLDER_ID="your-google-drive-folder-id"
   ```

2. **Obtain OAuth Tokens**:
   When you first run the bot, the system will prompt you to log in with your Google account. This will generate `sheet_token.json` and `drive_token.json` files to authenticate access to Google Sheets and Drive.

## Running the Bot

1. **Run the bot**:
   Once everything is set up, navigate to the src folder and run the bot using:
   ```bash
   cd src
   python telebot.py
   ```

1. **Authorization**:
   - When running the bot for the first time, a browser window will pop up, prompting you to log in and authorize the Google Sheets and Drive APIs. 
   - This will create the `sheet_token.json` and `drive_token.json` files for future sessions.

2. **Bot Activation**:
   Once the bot is running, start interacting with it by searching for it in Telegram with the username `@nepalfinancebot`.


## File Structure

```
NEPAL-FINANCE/
│
├── src/
│   ├── __pycache__/                # Python cache files (auto-generated)
│   ├── drive_connector.py          # Module for handling Google Drive API
│   ├── error_handling.py           # Error handling utilities
│   ├── telebot.py                  # Main bot file
│   ├── utils.py                    # Utility functions for Google Sheets and Drive
│
├── venv/                           # Virtual environment (dependencies)
├── .env                            # Environment variables for bot configuration
├── .gitignore                      # Git ignore file (to ignore unnecessary files)
├── credentials.json                # Google API credentials (for authentication)
├── drive_token.json                # Token for Google Drive API (auto-generated after first run)
├── sheet_token.json                # Token for Google Sheets API (auto-generated after first run)
├── README.md                       # Project documentation
├── requirements.txt                # Python dependencies
```


## Contributing

> **Note**: Please contribute with PRs... Code is quite bad atm, sorry.

### How to Contribute

1. **Fork the Repository**:
   - Navigate to the [repository page](https://github.com/your-username/nepal-finance) on GitHub and click the **Fork** button.
   - This will create a copy of the repository under your own GitHub account.

2. **Clone Your Fork**:
   - Clone the forked repository to your local machine using the following command:
     ```bash
     git clone https://github.com/your-username/nepal-finance.git
     cd nepal-finance
     ```

3. **Create a New Branch**:
   - Create a new branch to work on a specific feature or fix. Make sure to name the branch descriptively so it’s clear what you're working on:
     ```bash
     git checkout -b feature/your-feature-name
     ```

4. **Make Your Changes**:
   - Implement your feature or bug fix in the newly created branch.
   - Commit your changes using clear and concise commit messages:
     ```bash
     git add .
     git commit -m "Add feature/fix description here"
     ```

5. **Push Your Branch**:
   - Push the changes to your forked repository on GitHub:
     ```bash
     git push origin feature/your-feature-name
     ```

6. **Create a Pull Request (PR)**:
   - After pushing your branch, go to your forked repository on GitHub.
   - You will see a prompt to create a pull request. Click on that button or go to the **Pull Requests** tab, then click **New Pull Request**.
   - Compare your branch with the `main` branch of the original repository and submit the pull request with a clear title and description of the changes.

7. **Wait for Review**:
   - If the changes are alright the PR will be merged into the main repository

### Linting

Before submitting a pull request, please ensure your code follows the project's coding style by using [black](https://github.com/psf/black). This helps to keep the formatting consistent across the project.

To format your code with `black`, run the following command:

```bash
black .
```

This will automatically format your code according to the `black` style guide.


### Working with python-telegram-bot
- [Introduction to the API](https://github.com/python-telegram-bot/v13.x-wiki/wiki/Introduction-to-the-API)
- [Tutorial - Your first bot](https://github.com/python-telegram-bot/v13.x-wiki/wiki/Extensions-%E2%80%93-Your-first-Bot)
- [python-telegram-bot v13.x wiki](https://github.com/python-telegram-bot/v13.x-wiki/wiki)
- [python-telegram-bot v13.15 documentation](https://docs.python-telegram-bot.org/en/v13.15/)
