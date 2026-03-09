# Telegram Expense Bot

Prosty bot do zarządzania wydatkami na Telegramie, napisany w Pythonie przy użyciu `python-telegram-bot`.

## Funkcje

-   **Dodawanie wydatków (`/add`):** Pozwala wprowadzić kwotę, wybrać kategorię i dodać krótki opis.
-   **Zarządzanie kategoriami (`/cat`):** Każdy użytkownik może mieć własną listę kategorii.
    -   `/cat add <nazwa>` - dodaje nową kategorię.
    -   `/cat delete <nazwa>` - usuwa kategorię.
    -   `/cat list` - wyświetla Twoje kategorie.
-   **Inteligentne sortowanie:** Przy dodawaniu wydatku kategorie są sortowane od najczęściej używanych do najrzadziej (per użytkownik).
-   **Lista wydatków (`/list`):** Wyświetla ostatnie transakcje (domyślnie 5, można podać liczbę, np. `/list 10`).
-   **Raporty miesięczne (`/report`):** Generuje podsumowanie wydatków z podziałem na kategorie dla obecnego miesiąca, poprzedniego (`/report last`) lub konkretnego (`/report 2026-02`).
-   **Bezpieczeństwo:** Tylko użytkownicy dodani do `allowed_users.json` mogą korzystać z funkcji dodawania i przeglądania danych.

## Wymagania

-   Python 3.10+
-   Token bota od BotFather
-   Biblioteki z `requirements.txt`

## Instalacja

1. Sklonuj repozytorium.
2. Zainstaluj zależności: `pip install -r requirements.txt`.
3. Utwórz plik `.env` z tokenem: `TELEGRAM_TOKEN=twoj_token`.
4. Dodaj swoje Telegram ID do `allowed_users.json` (np. `[123456789]`).
5. Uruchom bota: `python main.py`.

## Struktura plików

-   `main.py` - główny kod bota.
-   `expenses.json` - baza danych wydatków (pogrupowana po `user_id`).
-   `categories.json` - personalizowane kategorie użytkowników.
-   `allowed_users.json` - lista ID użytkowników z dostępem.
-   `.env` - token bota (zignorowany w git).
