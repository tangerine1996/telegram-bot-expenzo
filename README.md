# Telegram Expense Tracker Bot

A simple and interactive Telegram bot to track personal expenses, categorize them, and generate monthly reports.

## Features

- **Access Control**: Restricted access for specific user IDs (configured in `main.py`).
- **Interactive Expense Entry**: Use `/add` to start a conversation-based form to log expenses.
  - Input amount (PLN).
  - Select category from inline buttons (Food, Transport, Entertainment, Shopping, Other).
  - Add a short description.
- **Expense History**: Use `/list [n]` to see your recent transactions.
- **Monthly Reports**: Use `/report` to see a summary of spending by category.
  - `/report`: Current month.
  - `/report last`: Previous month.
  - `/report YYYY-MM`: Specific month (e.g., `/report 2026-02`).
- **User Identification**: `/myid` command available for everyone to find their Telegram ID.
- **Timezone Aware**: All entries are recorded using the `Europe/Warsaw` timezone.
- **JSON Storage**: Data is saved in a local `expenses.json` file.

## Prerequisites

- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Setup

1. **Clone the repository** (or copy the files).

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytz
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory and add your bot token:
   ```env
   TELEGRAM_TOKEN=your_bot_token_here
   ```

4. **Authorize Users**:
   Add authorized Telegram IDs to the `allowed_users.json` file in JSON format:
   ```json
   [
       123456789,
       987654321
   ]
   ```

## Usage

Run the bot using:
```bash
python main.py
```

### Commands
- `/add` - Start adding a new expense (Authorized only).
- `/list [number]` - List last N expenses (Authorized only).
- `/report [YYYY-MM|last]` - Show monthly report (Authorized only).
- `/myid` - Show your Telegram User ID (Public).
- `/cancel` - Cancel the current interactive operation.

## Data Structure
Expenses are stored in `expenses.json` in the following format:
```json
{
    "user_id": 1234567890,
    "datetime": "2026-03-06 17:45:12",
    "amount": 42.50,
    "category": "Food",
    "description": "Lunch at work"
}
```

## License
MIT
