import os
import json
import logging
import pytz
import datetime
from datetime import datetime as dt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

# Konfiguracja logowania
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Pobranie katalogu bazowego bota (tam gdzie jest main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

# Funkcja do wczytywania uprawnionych ID użytkowników
def load_allowed_users():
    file_path = get_path('allowed_users.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.error(f"Błąd odczytu {file_path}. Zwracam pustą listę.")
                return []
    return []


# Kategorie domyślne
DEFAULT_CATEGORIES = ["Jedzenie", "Transport", "Rozrywka", "Zakupy", "Inne"]

# Stany rozmowy dla ConversationHandler
AMOUNT, CATEGORY, DESCRIPTION, CONFIRM = range(4)

def load_user_categories(user_id):
    """Wczytuje kategorie dla konkretnego użytkownika. Jeśli brak, zwraca domyślne."""
    file_path = get_path('categories.json')
    user_id_str = str(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                all_cats = json.load(f)
                cats = all_cats.get(user_id_str, DEFAULT_CATEGORIES.copy())
                logging.info(f"Wczytano kategorie dla {user_id_str}: {cats}")
                return cats
            except json.JSONDecodeError:
                logging.error(f"Błąd odczytu {file_path}")
                return DEFAULT_CATEGORIES.copy()
    return DEFAULT_CATEGORIES.copy()

def save_user_categories(user_id, categories):
    """Zapisuje listę kategorii dla użytkownika."""
    file_path = get_path('categories.json')
    user_id_str = str(user_id)
    all_cats = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                all_cats = json.load(f)
            except json.JSONDecodeError:
                all_cats = {}
    
    all_cats[user_id_str] = categories
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_cats, f, indent=4, ensure_ascii=False)
    logging.info(f"Zapisano kategorie dla {user_id_str} do {file_path}")

async def post_init(application):
    """Konfiguruje menu komend widoczne w Telegramie przy starcie bota."""
    commands = [
        BotCommand("add", "Dodaj nowy wydatek"),
        BotCommand("list", "Lista ostatnich wydatków"),
        BotCommand("report", "Raport miesięczny"),
        BotCommand("cat", "Kategorie: /cat add, /cat delete, /cat list"),
        BotCommand("myid", "Pokaż moje Telegram ID"),
        BotCommand("cancel", "Anuluj obecną operację")
    ]
    await application.bot.set_my_commands(commands)

async def cat_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zarządza kategoriami użytkownika: add, delete, list."""
    user_id = update.effective_user.id
    if user_id not in load_allowed_users():
        return

    if not context.args:
        await update.message.reply_text(
            "Użycie:\n"
            "/cat add <nazwa> - dodaje kategorię\n"
            "/cat delete <nazwa> - usuwa kategorię\n"
            "/cat list - lista Twoich kategorii"
        )
        return

    subcommand = context.args[0].lower()
    user_cats = load_user_categories(user_id)

    if subcommand == "add":
        if len(context.args) < 2:
            await update.message.reply_text("Podaj nazwę kategorii do dodania.")
            return
        new_cat = " ".join(context.args[1:])
        if new_cat in user_cats:
            await update.message.reply_text(f"Kategoria '{new_cat}' już istnieje.")
        else:
            user_cats.append(new_cat)
            save_user_categories(user_id, user_cats)
            await update.message.reply_text(f"Dodano kategorię: {new_cat}")

    elif subcommand == "delete":
        if len(context.args) < 2:
            await update.message.reply_text("Podaj nazwę kategorii do usunięcia.")
            return
        cat_to_del = " ".join(context.args[1:])
        if cat_to_del in user_cats:
            user_cats.remove(cat_to_del)
            save_user_categories(user_id, user_cats)
            await update.message.reply_text(f"Usunięto kategorię: {cat_to_del}")
        else:
            await update.message.reply_text(f"Nie znaleziono kategorii: {cat_to_del}")

    elif subcommand == "list":
        cats_str = "\n".join([f"• {c}" for c in user_cats])
        await update.message.reply_text(f"Twoje kategorie:\n{cats_str}")
    
    else:
        await update.message.reply_text("Nieznana podkomenda. Użyj add, delete lub list.")

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generuje raport wydatków z podziałem na kategorie dla danego miesiąca."""
    user_id = update.effective_user.id
    if user_id not in load_allowed_users():
        return

    poland_tz = pytz.timezone('Europe/Warsaw')
    now = dt.now(poland_tz)
    
    target_month = now.strftime("%Y-%m") # Domyślnie obecny miesiąc

    if context.args:
        arg = context.args[0].lower()
        if arg == "last":
            # Obliczanie poprzedniego miesiąca
            first_day_of_current = now.replace(day=1)
            last_day_of_prev = first_day_of_current - datetime.timedelta(days=1)
            target_month = last_day_of_prev.strftime("%Y-%m")
        elif len(arg) == 7 and arg[4] == '-':
            # Sprawdzenie formatu RRRR-MM
            target_month = arg
        else:
            await update.message.reply_text("Użyj formatu RRRR-MM lub 'last'. Generuję raport dla obecnego miesiąca.")

    file_path = get_path('expenses.json')
    if not os.path.exists(file_path):
        await update.message.reply_text("Brak zapisanych wydatków.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            expenses = json.load(f)
        except json.JSONDecodeError:
            await update.message.reply_text("Błąd odczytu bazy danych.")
            return

    # Filtrowanie po user_id i miesiącu
    user_id_str = str(user_id)
    user_expenses = expenses.get(user_id_str, [])
    
    filtered_expenses = [
        e for e in user_expenses 
        if e.get('datetime', '').startswith(target_month)
    ]

    if not filtered_expenses:
        await update.message.reply_text(f"Nie znaleziono wydatków dla okresu: {target_month}")
        return

    # Sumowanie po kategoriach
    report_data = {}
    total_sum = 0
    for exp in filtered_expenses:
        cat = exp.get('category', 'Inne')
        amt = exp.get('amount', 0)
        report_data[cat] = report_data.get(cat, 0) + amt
        total_sum += amt

    # Budowanie wiadomości
    response = f"📅 **Raport za: {target_month}**\n\n"
    for cat, sum_amt in sorted(report_data.items(), key=lambda x: x[1], reverse=True):
        response += f"• **{cat}**: {sum_amt:.2f} PLN\n"
    
    response += f"\n💰 **RAZEM: {total_sum:.2f} PLN**"

    await update.message.reply_text(response, parse_mode='Markdown')

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wyświetla listę ostatnich wydatków użytkownika."""
    user_id = update.effective_user.id
    if user_id not in load_allowed_users():
        return

    # Pobieranie argumentu (liczba wydatków)
    n = 5 # domyślnie
    if context.args:
        try:
            val = int(context.args[0])
            if 1 <= val <= 100:
                n = val
            else:
                await update.message.reply_text("Liczba musi być z zakresu od 1 do 100. Używam domyślnej wartości 5.")
        except ValueError:
            await update.message.reply_text("Podaj poprawną liczbę. Używam domyślnej wartości 5.")

    file_path = get_path('expenses.json')
    if not os.path.exists(file_path):
        await update.message.reply_text("Brak zapisanych wydatków.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            expenses = json.load(f)
        except json.JSONDecodeError:
            await update.message.reply_text("Błąd odczytu bazy danych.")
            return

    # Filtrowanie wydatków dla tego użytkownika
    user_id_str = str(user_id)
    user_expenses = expenses.get(user_id_str, [])
    
    if not user_expenses:
        await update.message.reply_text("Nie znaleziono Twoich wydatków.")
        return

    # Pobieranie ostatnich n wydatków
    last_n = user_expenses[-n:]
    # Odwracamy, żeby najnowsze były na górze
    last_n.reverse()

    response = f"📊 **Ostatnie {len(last_n)} wydatków:**\n\n"
    for i, exp in enumerate(last_n, 1):
        # Pobieramy tylko część daty (pierwsze 10 znaków: RRRR-MM-DD)
        full_dt = exp.get('datetime', 'N/A')
        date_only = full_dt[:10] if len(full_dt) >= 10 else full_dt
        
        cat = exp.get('category', 'Inne')
        amt = exp.get('amount', 0)
        desc = exp.get('description', '')
        
        # Nowy format: RRRR-MM-DD - kategoria - kwota - opis
        response += f"{i}. `{date_only}` - **{cat}** - **{amt} PLN** - {desc}\n"

    await update.message.reply_text(response, parse_mode='Markdown')

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zwraca ID użytkownika każdemu, kto wpisze /myid."""
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Twoje Telegram ID to: {user_id}")

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicjuje proces dodawania wydatku."""
    if update.effective_user.id not in load_allowed_users():
        logging.info(f"Odmowa /add dla użytkownika: {update.effective_user.id}")
        return ConversationHandler.END
    
    await update.message.reply_text("Podaj kwotę w PLN (np. 25.50):")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pobiera kwotę i prosi o kategorię."""
    try:
        amount_str = update.message.text.replace(',', '.')
        amount = float(amount_str)
        context.user_data['amount'] = amount
        
        user_cats = load_user_categories(update.effective_user.id)
        keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in user_cats]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("Wybierz kategorię:", reply_markup=reply_markup)
        return CATEGORY
    except ValueError:
        await update.message.reply_text("Błędny format. Wpisz liczbę (np. 12 lub 12.50):")
        return AMOUNT

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pobiera kategorię i prosi o opis."""
    query = update.callback_query
    await query.answer()
    context.user_data['category'] = query.data
    
    await query.edit_message_text(f"Wybrana kategoria: {query.data}\nTeraz wpisz krótki opis wydatku:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pobiera opis i pokazuje podsumowanie z przyciskiem Add."""
    context.user_data['description'] = update.message.text
    
    summary = (
        f"📝 **Podsumowanie wydatku:**\n"
        f"💰 Kwota: {context.user_data['amount']} PLN\n"
        f"📂 Kategoria: {context.user_data['category']}\n"
        f"ℹ️ Opis: {context.user_data['description']}"
    )
    
    keyboard = [[InlineKeyboardButton("Dodaj ✅", callback_data="confirm_add")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM

async def confirm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zapisuje dane do pliku JSON po kliknięciu przycisku."""
    query = update.callback_query
    await query.answer()
    
    # Używamy strefy czasowej dla Polski
    poland_tz = pytz.timezone('Europe/Warsaw')
    now = dt.now(poland_tz)
    user_id_str = str(update.effective_user.id)
    
    expense_data = {
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "amount": context.user_data['amount'],
        "category": context.user_data['category'],
        "description": context.user_data['description']
    }
    
    # Wczytywanie istniejących danych
    file_path = get_path('expenses.json')
    expenses = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                expenses = json.load(f)
                if not isinstance(expenses, dict):
                    expenses = {} # Reset if not dict
            except json.JSONDecodeError:
                expenses = {}
    
    # Dodawanie nowego wpisu
    if user_id_str not in expenses:
        expenses[user_id_str] = []
    
    expenses[user_id_str].append(expense_data)
    
    # Zapis do pliku
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(expenses, f, indent=4, ensure_ascii=False)
    
    await query.edit_message_text(f"✅ Wydatek został zapisany w {file_path}!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Anuluje proces."""
    await update.message.reply_text("Anulowano dodawanie wydatku.")
    return ConversationHandler.END

if __name__ == '__main__':
    # Pobieranie tokena z pliku .env
    token = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('TELEGRAM_TOKEN='):
                    token = line.split('=')[1].strip()
    
    if not token:
        print('BŁĄD: Nie znaleziono TELEGRAM_TOKEN w pliku .env!')
        exit(1)
        
    # Inicjalizacja aplikacji z post_init dla menu komend
    application = ApplicationBuilder().token(token).post_init(post_init).build()
    
    # Konfiguracja obsługi formularza /add (ConversationHandler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', start_add)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CATEGORY: [CallbackQueryHandler(get_category)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CONFIRM: [CallbackQueryHandler(confirm_add, pattern='^confirm_add$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Rejestracja handlerów
    application.add_handler(CommandHandler('myid', my_id))
    application.add_handler(CommandHandler('list', list_expenses))
    application.add_handler(CommandHandler('report', generate_report))
    application.add_handler(CommandHandler('cat', cat_manager))
    application.add_handler(conv_handler)
    
    print('Bot uruchomiony pomyślnie.')
    print('Menu komend zostanie zaktualizowane w aplikacji Telegram.')
    application.run_polling()
