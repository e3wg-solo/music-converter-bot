import requests
import re
# from langdetect import detect  # Если не нужно, можно удалить
from yandex_music import Client
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from fuzzywuzzy import fuzz
import asyncio
from typing import Optional
import time
from supabase import create_client, Client as SupabaseClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import traceback

print("🚀 Бот запускается...")

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# SSH Configuration
SSH_HOST = os.getenv("SSH_HOST")
SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PRIVATE_KEY = os.getenv("SSH_PRIVATE_KEY")

print(f"✅ Конфигурация загружена")

# 🔹 Инициализация API-клиентов
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
router = Router()
client = Client(YANDEX_TOKEN).init()
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# Проверка подключения к Supabase
try:
    test_response = supabase.table("requests").select("count").execute()
    print("✅ Подключение к Supabase успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения к Supabase: {str(e)}")

print("✅ Библиотеки загружены, создаём маршруты...")

class ProxyManager:
    def __init__(self):
        proxy_string = "156.246.145.173:63732:JHS4g133:6gQdk49S"
        host, port, username, password = proxy_string.split(":")
        self.http_proxy_url = f"http://{username}:{password}@{host}:{port}"
        self.socks_proxy_url = f"socks5://{username}:{password}@{host}:{port}"  # Используем тот же порт
        self.use_socks = True  # По умолчанию используем SOCKS
        self.verify_proxy()
        
    def verify_proxy(self):
        try:
            print("🔄 Проверяем SOCKS5 прокси...")
            response = requests.get(
                "https://api.spotify.com/v1/ping",
                proxies={"http": self.socks_proxy_url, "https": self.socks_proxy_url},
                timeout=10
            )
            print(f"✅ SOCKS5 прокси работает! Статус: {response.status_code}")
            self.use_socks = True
        except Exception as e:
            print(f"⚠️ Ошибка при проверке SOCKS5 прокси: {e}")
            print("🔄 Пробуем HTTP прокси...")
            try:
                response = requests.get(
                    "https://api.spotify.com/v1/ping",
                    proxies={"http": self.http_proxy_url, "https": self.http_proxy_url},
                    timeout=10
                )
                print(f"✅ HTTP прокси работает! Статус: {response.status_code}")
                self.use_socks = False
            except Exception as e:
                print(f"❌ HTTP прокси тоже не работает: {e}")
        
    def get_proxy(self):
        proxy_url = self.socks_proxy_url if self.use_socks else self.http_proxy_url
        return {
            "http": proxy_url,
            "https": proxy_url
        }

proxy_manager = ProxyManager()

# 🔹 Функция для получения токена Spotify API
def get_spotify_token():
    print("🔑 Запрашиваем токен Spotify...")
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=data, 
            auth=auth,
            proxies=proxy_manager.get_proxy(),
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get("access_token")
        
        print(f"❌ Ошибка получения токена Spotify: {response.text}")
        return None
            
    except Exception as e:
        print(f"❌ Ошибка при получении токена: {e}")
        return None


# 🔹 Получаем информацию о треке из Spotify (по URL)
def get_track_info(spotify_url):
    print(f"🎵 Получаем информацию о треке: {spotify_url}")
    match = re.search(r"track/([a-zA-Z0-9]+)", spotify_url)
    if not match:
        print("❌ Ошибка: Не удалось извлечь track_id из ссылки!")
        return None

    track_id = match.group(1)
    token = get_spotify_token()
    if not token:
        print("❌ Ошибка: Нет токена Spotify!")
        return None

    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            url, 
            headers=headers,
            proxies=proxy_manager.get_proxy(),
            timeout=10
        )
        print(f"📡 Статус ответа Spotify API: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Ошибка API Spotify: {response.text}")
            return None
            
        data = response.json()
        
        if "error" in data:
            print(f"❌ Ошибка в ответе Spotify: {data['error']}")
            return None

        if "name" in data and "artists" in data:
            artist_name = data["artists"][0]["name"]
            print(f"✅ Трек найден: {data['name']} - {artist_name}")
            return {"name": data["name"], "artist": artist_name}

        print(f"❌ Неожиданный формат ответа: {data}")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка при запросе к Spotify API: {e}")
        return None


# 🔹 Поиск трека в Яндекс.Музыке
def search_yandex_music(track_name, artist_name):
    print(f"🔍 Ищем '{track_name} - {artist_name}' в Яндекс.Музыке...")
    
    # Сначала пробуем точный поиск
    results = client.search(f"{track_name} {artist_name}", type_="track")
    
    if not (results.tracks and results.tracks.results):
        # Если точный поиск не дал результатов, пробуем искать только по названию
        results = client.search(track_name, type_="track")
    
    if results.tracks and results.tracks.results:
        # Ищем лучшее совпадение среди первых 10 результатов
        best_match = None
        best_score = 0
        
        for track in results.tracks.results[:10]:
            track_title = track.title.lower()
            track_artist = track.artists[0].name.lower()
            
            name_score = fuzz.ratio(track_title, track_name.lower())
            artist_score = fuzz.ratio(track_artist, artist_name.lower())
            total_score = (name_score * 0.6) + (artist_score * 0.4)
            
            if total_score > best_score:
                best_score = total_score
                best_match = track
        
        if best_match and best_score > 70:
            track_link = f"https://music.yandex.ru/album/{best_match.albums[0].id}/track/{best_match.id}"
            print(f"✅ Найден трек в Яндекс.Музыке: {track_link} (Совпадение: {best_score}%)")
            return track_link
    
    print(f"❌ Не удалось найти трек '{track_name}' в Яндекс.Музыке!")
    return None


# 🔹 Получаем информацию о треке из Яндекс.Музыки (по URL)
def get_yandex_track_info(yandex_url):
   print(f"🎵 Получаем информацию о треке из Яндекс.Музыки: {yandex_url}")
   match = re.search(r"track/(\d+)", yandex_url)
   if not match:
       print("❌ Ошибка: Не удалось извлечь track_id из ссылки!")
       return None


   track_id = match.group(1)
   try:
       track = client.tracks(track_id)[0]
       track_name = track.title
       artist_name = track.artists[0].name
       print(f"✅ Трек найден: {track_name} - {artist_name}")


       # Обрезаем, если название заканчивается " - ArtistName" (учитываем разные тире)
       pattern = re.compile(
           rf"\s*[-–—]\s*{re.escape(artist_name)}\s*$",
           re.IGNORECASE
       )
       if pattern.search(track_name):
           track_name = pattern.sub("", track_name).strip()


       return {"name": track_name, "artist": artist_name}
   except Exception as e:
       print(f"❌ Ошибка при получении данных о треке: {e}")
       return None


# 🔹 Поиск трека в Spotify
def search_spotify(track_name, artist_name):
    print(f"🔍 Ищем '{track_name} - {artist_name}' в Spotify...")
    token = get_spotify_token()
    if not token:
        return None

    def clean_query_term(term):
        term = re.sub(r'[&+\-\(\)]', ' ', term)
        return ' '.join(term.split())

    clean_track = clean_query_term(track_name)
    clean_artist = clean_query_term(artist_name)
    
    search_queries = [
        f"track:\"{track_name}\" artist:\"{artist_name}\"",
        f"{track_name} {artist_name}",
        f"{clean_track} {clean_artist}"
    ]
    
    best_match = None
    best_score = 0
    
    for query in search_queries:
        url = f"https://api.spotify.com/v1/search?q={requests.utils.quote(query)}&type=track&limit=50"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(
                url, 
                headers=headers,
                proxies=proxy_manager.get_proxy(),
                timeout=10
            ).json()
            
            if not response.get("tracks") or not response["tracks"]["items"]:
                continue
                
            for track in response["tracks"]["items"]:
                spotify_track_name = track["name"].lower()
                
                artist_found = False
                for artist in track["artists"]:
                    if fuzz.ratio(artist["name"].lower(), artist_name.lower()) > 85:
                        artist_found = True
                        break
                
                normalized_spotify = clean_query_term(spotify_track_name).lower()
                normalized_search = clean_query_term(track_name).lower()
                
                name_score = max(
                    fuzz.ratio(spotify_track_name, track_name.lower()),
                    fuzz.ratio(normalized_spotify, normalized_search)
                )
                
                total_score = name_score
                if artist_found:
                    total_score += 25
                
                if total_score > best_score:
                    best_score = total_score
                    best_match = track
                    
        except Exception as e:
            print(f"❌ Ошибка при поиске в Spotify: {e}")
            continue

    if best_match and best_score > 70:
        track_link = best_match["external_urls"]["spotify"]
        print(f"✅ Найден трек в Spotify: {track_link} (Совпадение: {best_score}%)")
        return track_link

    print("❌ Не удалось найти точное совпадение!")
    return None


class Statistics:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def log_request(self, user_id, username, source_service, target_service, track_name, status, error_message=None):
        """Логирование запроса в базу данных"""
        try:
            data = {
                "user_id": str(user_id),
                "username": username or "unknown",
                "source_service": source_service,
                "target_service": target_service,
                "track_name": track_name,
                "status": status,
                "error_message": error_message,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            print(f"📝 Логируем запрос в Supabase: {data}")
            
            # Добавляем больше информации об ошибках
            try:
                response = self.supabase.table("requests").insert(data).execute()
                print(f"✅ Ответ от Supabase: {response}")
                if hasattr(response, 'error') and response.error:
                    print(f"❌ Ошибка Supabase при логировании: {response.error}")
                    return None
                    
                print(f"✅ Запрос успешно залогирован в Supabase")
                return response.data
            except Exception as insert_error:
                print(f"❌ Ошибка при выполнении insert: {str(insert_error)}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при подготовке данных: {str(e)}")
            return None
    
    async def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        try:
            response = self.supabase.table("requests")\
                .select("*")\
                .eq("user_id", str(user_id))\
                .execute()
            return response.data
        except Exception as e:
            print(f"❌ Ошибка при получении статистики: {e}")
            return []
    
    async def get_total_stats(self):
        """Получение общей статистики"""
        try:
            response = self.supabase.table("requests")\
                .select("*")\
                .execute()
            
            data = response.data
            total_requests = len(data)
            successful = len([s for s in data if s['status'] == 'success'])
            failed = len([s for s in data if s['status'] == 'error'])
            not_found = len([s for s in data if s['status'] == 'not_found'])
            unique_users = len(set(s['user_id'] for s in data))
            
            return {
                "total": total_requests,
                "success": successful,
                "error": failed,
                "not_found": not_found,
                "unique_users": unique_users
            }
        except Exception as e:
            print(f"❌ Ошибка при получении общей статистики: {e}")
            return {}


stats = Statistics(supabase)

# --- Обработчики ---


@router.message(Command("start"))
async def start(message: types.Message):
   print("📩 Получена команда /start")
   await message.answer("Привет! Отправь мне ссылку на песню из Spotify или Яндекс.Музыки, и я найду её аналог в другом сервисе.")


# 🔹 Обработчик ссылок на Spotify (Spotify → Яндекс)
@router.message(lambda message: "spotify.com/track" in message.text)
async def convert_spotify_to_yandex(message: types.Message):
    print(f"🔎 Получена ссылка: {message.text}")
    await message.answer("🔎 Ищу песню в Яндекс.Музыке...")

    track_info = get_track_info(message.text)
    if not track_info:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="spotify",
            target_service="yandex",
            track_name="unknown",
            status="error",
            error_message="Failed to get track info"
        )
        await message.answer("❌ Не удалось получить данные о треке.")
        return

    yandex_link = search_yandex_music(track_info['name'], track_info['artist'])
    if yandex_link:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="spotify",
            target_service="yandex",
            track_name=f"{track_info['name']} - {track_info['artist']}",
            status="success"
        )
        await message.answer(
            f"🎵 Найдено!\n[{track_info['name']} — {track_info['artist']}]({yandex_link})",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="spotify",
            target_service="yandex",
            track_name=f"{track_info['name']} - {track_info['artist']}",
            status="not_found"
        )
        await message.answer(
            f"❌ Не удалось найти\n```\n{track_info['name']} - {track_info['artist']}\n```\nв Яндекс.Музыке.",
            parse_mode=ParseMode.MARKDOWN
        )


# 🔹 Обработчик ссылок на Яндекс (Яндекс → Spotify)
@router.message(lambda message: any(x in message.text for x in ["music.yandex.ru/track", "music.yandex.ru/album"]))
async def convert_yandex_to_spotify(message: types.Message):
    print(f"🔎 Получена ссылка: {message.text}")
    await message.answer("🔎 Ищу песню в Spotify...")

    track_info = get_yandex_track_info(message.text)
    if not track_info:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="yandex",
            target_service="spotify",
            track_name="unknown",
            status="error",
            error_message="Failed to get track info"
        )
        await message.answer("❌ Не удалось получить данные о треке.")
        return

    spotify_link = search_spotify(track_info['name'], track_info['artist'])
    if spotify_link:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="yandex",
            target_service="spotify",
            track_name=f"{track_info['name']} - {track_info['artist']}",
            status="success"
        )
        await message.answer(
            f"🎵 Найдено!\n[{track_info['name']} — {track_info['artist']}]({spotify_link})",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await stats.log_request(
            user_id=message.from_user.id,
            username=message.from_user.username,
            source_service="yandex",
            target_service="spotify",
            track_name=f"{track_info['name']} - {track_info['artist']}",
            status="not_found"
        )
        await message.answer(
            f"❌ Не удалось найти\n```\n{track_info['name']} - {track_info['artist']}\n```\nв Spotify.",
            parse_mode=ParseMode.MARKDOWN
        )


@router.message(Command("stats"))
async def show_stats(message: types.Message):
    """Показать статистику пользователя"""
    try:
        print(f"📊 Запрошена статистика пользователем {message.from_user.id}")
        user_stats = await stats.get_user_stats(message.from_user.id)
        
        total_requests = len(user_stats)
        successful = len([s for s in user_stats if s['status'] == 'success'])
        failed = len([s for s in user_stats if s['status'] == 'error'])
        not_found = len([s for s in user_stats if s['status'] == 'not_found'])
        
        stats_message = (
            f"📊 Ваша статистика:\n"
            f"Всего запросов: {total_requests}\n"
            f"Успешных: {successful}\n"
            f"Не найдено: {not_found}\n"
            f"Ошибок: {failed}"
        )
        
        await message.answer(stats_message)
        print(f"✅ Статистика успешно отправлена пользователю {message.from_user.id}")
    except Exception as e:
        error_msg = f"❌ Ошибка при получении статистики: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        await message.answer("❌ Произошла ошибка при получении статистики. Попробуйте позже.")


@router.message(Command("admin_stats"))
async def show_admin_stats(message: types.Message):
    """Показать общую статистику (только для админов)"""
    try:
        user_id = message.from_user.id
        print(f"👤 Запрос админ-статистики от пользователя {user_id}")
        
        ADMIN_IDS = [81078202]  # Ваш ID
        
        if user_id not in ADMIN_IDS:
            print(f"⛔️ Отказано в доступе пользователю {user_id}")
            await message.answer("⛔️ У вас нет доступа к этой команде")
            return
            
        print("✅ Доступ разрешен, получаем статистику...")
        total_stats = await stats.get_total_stats()
        stats_message = (
            f"📊 Общая статистика:\n"
            f"Всего пользователей: {total_stats.get('unique_users', 0)}\n"
            f"Всего запросов: {total_stats.get('total', 0)}\n"
            f"Успешных: {total_stats.get('success', 0)}\n"
            f"Не найдено: {total_stats.get('not_found', 0)}\n"
            f"Ошибок: {total_stats.get('error', 0)}"
        )
        
        await message.answer(stats_message)
        print(f"✅ Админ-статистика успешно отправлена")
    except Exception as e:
        error_msg = f"❌ Ошибка при получении админ-статистики: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        await message.answer("❌ Произошла ошибка при получении статистики. Попробуйте позже.")

# 🔹 Запуск бота
async def main():
    print("🚀 Бот готов к запуску!")
    
    # Проверяем подключение к Telegram
    try:
        me = await bot.get_me()
        print(f"✅ Подключение к Telegram успешно! Имя бота: {me.full_name}")
    except Exception as e:
        print(f"❌ Ошибка при подключении к Telegram: {e}")
        return
    
    # Полностью сбрасываем состояние бота
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Вебхук успешно удален")
    except Exception as e:
        print(f"❌ Ошибка при удалении вебхука: {e}")
    
    # Настраиваем и запускаем бота
    dp.include_router(router)
    try:
        print("🚀 Запускаем получение обновлений...")
        await dp.start_polling(bot, allowed_updates=["message"])
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())



