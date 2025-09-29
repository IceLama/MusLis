from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import json
import os

# Настройка опций браузера
chrome_options = Options()
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
# chrome_options.add_argument("--headless=new")  # Раскомментируй для headless
# Имя исполнителя (замени на нужного)
artist_name = "Taylor Swift"
playlist_url = "https://music.youtube.com/playlist?list=PLP6eWgIGaOuqHpR967XffYlTlHdRrMNOI"
# Чтение учетных данных из файла
try:
    with open("credentials.json", "r") as f:
        accounts = json.load(f)
    print(f"Загружено {len(accounts)} аккаунтов из credentials.json")
except FileNotFoundError:
    print("Ошибка: Файл credentials.json не найден")
    accounts = [
        {"email": input("Введите email для аккаунта 1: "), "password": input("Введите пароль для аккаунта 1: ")}
    ]
except KeyError:
    print("Ошибка: Неверный формат credentials.json (нужны 'email' и 'password' для каждого аккаунта)")
    accounts = [
        {"email": input("Введите email для аккаунта 1: "), "password": input("Введите пароль для аккаунта 1: ")}
    ]

# Список для хранения экземпляров браузеров
drivers = []

# Цикл по каждому аккаунту
for i, account in enumerate(accounts, 1):
    print(f"\nОбработка аккаунта {i}: {account['email']}")

    # Запуск браузера для каждого аккаунта
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    drivers.append(driver)  # Сохраняем браузер

    try:
        driver.get("https://music.youtube.com/")
        wait = WebDriverWait(driver, 30)

        # Шаг 1: Обработка cookies
        try:
            # Обработка cookies
            wait = WebDriverWait(driver, 20)
            accept_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Принять все' or contains(text(), 'Accept all')]")))
            driver.execute_script("arguments[0].click();", accept_button)
            time.sleep(3)
            print("Кнопка 'Принять все' нажата")
        except Exception as e:
            print(f"Не удалось найти или нажать кнопку cookies: {e}")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("HTML страницы сохранён в page_source.html для анализа")
            time.sleep(3)

        # Шаг 2: Авторизация
        try:
            sign_in_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(), 'Войти') or contains(@aria-label, 'Sign in')]")))
            print("Кнопка 'Войти' найдена, кликаем...")
            driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(2)

            # Ввод email
            email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(account["email"])
            email_input.send_keys(Keys.ENTER)
            time.sleep(3)

            # Ввод пароля
            password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            password_input.send_keys(account["password"])
            password_input.send_keys(Keys.ENTER)
            time.sleep(5)  # Ждём редиректа или 2FA

            print(f"Авторизация выполнена для {account['email']}")
        except Exception as e:
            print(f"Авторизация не требуется или ошибка для {account['email']}: {e}")

        # Шаг 3: Поиск исполнителя и запуск музыки
        try:
            # Переходим на URL плейлиста
            driver.get(playlist_url)
            time.sleep(5)  # Увеличено для загрузки

            # Ждём загрузки плеера
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "ytmusic-player-bar")))
            print(f"Страница плейлиста загружена для {account['email']}")

            # Проверяем, началось ли воспроизведение
            try:
                play_button = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                     "//ytmusic-play-button-renderer//button[@title='Play' or @title='Pause' or contains(@aria-label, 'Play all') or contains(@aria-label, 'Shuffle')]")))
                driver.execute_script("arguments[0].click();", play_button)
                print(f"Плейлист запущен для {account['email']}")
            except Exception as e:
                print(f"Кнопка воспроизведения не найдена, пробуем альтернативный селектор: {e}")
                # Альтернативный селектор для кнопки
                play_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'play-button') or contains(@aria-label, 'Play')]")))
                driver.execute_script("arguments[0].click();", play_button)
                print(f"Плейлист запущен (альтернативный селектор) для {account['email']}")

        except Exception as e:
            print(f"Ошибка при запуске плейлиста для {account['email']}: {e}")
            driver.save_screenshot(f"screenshot_playlist_{account['email']}.png")
            with open(f"page_source_playlist_{account['email']}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Скриншот и HTML сохранены для {account['email']}")
    except Exception as e:
        print(f"Общая ошибка для {account['email']}: {e}")
        with open(f"page_source_{account['email']}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML страницы сохранён в page_source_{account['email']}.html")

    # Закрытие браузера для этого аккаунта
    # driver.quit()
    print(f"Завершено для аккаунта {account['email']}")
    time.sleep(random.uniform(2, 5))  # Пауза между аккаунтами

# Ждём завершения (все браузеры открыты)
input("\nВсе аккаунты запущены! Нажмите Enter для закрытия всех браузеров...")

# Закрываем все браузеры
for driver in drivers:
    driver.quit()

print("Все аккаунты обработаны и браузеры закрыты!")
