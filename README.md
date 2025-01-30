**Dokumentacja projektu
Opis projektu
Projekt to aplikacja internetowa stworzona przy użyciu frameworka Flask, realizowana w ramach przedmiotu "Python w praktyce - web & deep learning". Jest to internetowe kasyno, które oferuje trzy gry losowe: ruletkę, blackjacka i kości. Użytkownicy mogą zakładać konto, logować się, zarządzać swoim kontem oraz uczestniczyć w grach.

Autorzy
•	Herbert Rabiega - 217313
•	Aleksander Polachowski - 217481
•	Mateusz Sapierzyński - 217438


Funkcjonalności
1.	Aplikacja we Flasku – backend aplikacji został stworzony w Pythonie z wykorzystaniem frameworka Flask.
2.	Połączenie z bazą danych
3.	System użytkowników – możliwość rejestracji konta oraz logowania użytkownika (z walidacją wieku – tylko osoby pełnoletnie mogą założyć konto).
4.	Wybór gry – użytkownicy mogą wybierać spośród trzech dostępnych gier: ruletki, blackjacka i kości.
5.	Zarządzanie finansami – możliwość wpłacania i wypłacania środków.
6.	Panel administratora – użytkownicy z rangą administratora mają dostęp do zakładki „Moje konto”, gdzie mogą przeglądać statystyki kasyna oraz edytować użytkowników. (np. login admin hasło admin123)


Struktura kodu (plik main.py)

Plik main.py pełni rolę głównego pliku aplikacji i zawiera następujące elementy:
•	Inicjalizacja aplikacji Flask – tworzenie instancji aplikacji.
•	Konfiguracja bazy danych – połączenie z bazą danych.
•	Modele użytkowników i danych – definicja struktur tabel w bazie danych.
•	Obsługa rejestracji i logowania – formularze oraz mechanizmy uwierzytelniania użytkowników.
•	Obsługa formularza dodawania danych – zapis danych do bazy.
•	Wyświetlanie danych – pobieranie zapisanych informacji z bazy i prezentacja użytkownikowi.
•	Obsługa gier – implementacja zasad gier kasynowych (ruletka, blackjack, kości) i logiki rozgrywki.
•	Obsługa płatności – implementacja mechanizmu wpłat i wypłat środków.
•	Panel administratora – moduł umożliwiający zarządzanie użytkownikami i przeglądanie statystyk.
•	Uruchomienie aplikacji – uruchomienie serwera Flask.

Plik requirements.txt zawiera listę wymaganych modułów, które należy zainstalować przed uruchomieniem aplikacji, np. Flask, Flask-SQLAlchemy, Flask-Login.
Wykorzystane technologie
•	Python, Flask – backend
•	SQL– baza danych
•	HTML– frontend


Uruchomienie aplikacji
Aby uruchomić aplikację, wykonaj następujące kroki:
1.	Zainstaluj wymagane biblioteki: 
pip install -r requirements.txt
2.	Uruchom aplikację: 
python main.py
3.	Otwórz przeglądarkę i przejdź do http://127.0.0.1:5000/.


Podsumowanie
Aplikacja spełnia wszystkie wymagania projektu, zapewniając użytkownikom możliwość rejestracji, logowania, wyboru gier oraz zarządzania środkami finansowymi. Jest to system oparty na Flasku i bazie danych. Dodatkowo oferuje funkcjonalność panelu administratora, który umożliwia zarządzanie użytkownikami oraz monitorowanie statystyk kasyna.

**
