# encoding: utf-8
import requests
import json
import logging
import os
import time
from datetime import datetime, timedelta

DOMAIN = 'tts_zalo'
TTS_apikey = 'apikey'
TTS_speed = 'speed'
TTS_speaker_id = 'speaker_id'
CONFIG_id_media_player = 'entity_id'
CONFIG_message = 'message'
ERROR_KEYS_FILE = 'custom_components/tts_zalo/__.json'

logger = logging.getLogger(__name__)
current_directory = os.getcwd()
target_directory = os.path.join(current_directory, 'www', DOMAIN)
os.makedirs(target_directory, exist_ok=True)
os.chmod(target_directory, 0o777)


def log_error_key(api_key):
    error_keys = {}
    if os.path.exists(ERROR_KEYS_FILE):
        with open(ERROR_KEYS_FILE, 'r') as f:
            error_keys = json.load(f)
    error_keys[api_key] = datetime.now().date().isoformat()
    with open(ERROR_KEYS_FILE, 'w') as f:
        json.dump(error_keys, f)

def clear_expired_keys():
    valid_keys = []
    if os.path.exists(ERROR_KEYS_FILE):
        with open(ERROR_KEYS_FILE, 'r') as f:
            error_keys = json.load(f)
        expiration_date = datetime.now().date() - timedelta(days=1)
        valid_keys = [
            key for key, date_str in error_keys.items()
            if datetime.fromisoformat(date_str).date() >= expiration_date
        ]
        error_keys = {key: date for key, date in error_keys.items() if key in valid_keys}
        with open(ERROR_KEYS_FILE, 'w') as f:
            json.dump(error_keys, f)
    return valid_keys

def setup(hass, cfg):
    expired_keys = clear_expired_keys()
    def zalo_tts(TTS):
        if not str(TTS.data.get(CONFIG_message, '')):
            logger.warning(f"[{DOMAIN}] Cần nhập nội dung thông báo tts_zalo")
            return
        Id_Speak_Hass = TTS.data.get(CONFIG_id_media_player)
        url = "https://api.zalo.ai/v1/tts/synthesize"
        payload = {
            'speaker_id': str(TTS.data.get(TTS_speaker_id, 1)),
            'speed': str(TTS.data.get(TTS_speed, 0.9)),
            'input': str(TTS.data.get(CONFIG_message)),
            'encode_type': 1
        }
        api_keys = [key for key in cfg[DOMAIN][TTS_apikey] if key not in expired_keys]
        for api_key in api_keys:
            headers = {
                'apikey': str(api_key),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            for attempt in range(3):
                try:
                    response = requests.post(url, headers=headers, data=payload)
                    response.raise_for_status()
                    result = response.json()
                    if result.get("error_code") == 0:
                        #logger.warning(f"[{DOMAIN}] Yêu cầu thành công!")
                        audio_url = result["data"]["url"]
                        #logger.warning(f"[{DOMAIN}] URL âm thanh: %s", audio_url)
                        for audio_attempt in range(3):
                            try:
                                audio_response = requests.get(audio_url)
                                audio_response.raise_for_status()
                                output_file = os.path.join(target_directory, f'{DOMAIN}.mp3')
                                with open(output_file, 'wb') as audio_file:
                                    audio_file.write(audio_response.content)
                                logger.warning(f"[{DOMAIN}] Tệp âm thanh tts_zalo: {output_file}")
                                Player_Hass = {
                                    'entity_id': Id_Speak_Hass,
                                    'media_content_id': f"/local/{DOMAIN}/{DOMAIN}.mp3",
                                    'media_content_type': 'music'
                                }
                                hass.services.call('media_player', 'play_media', Player_Hass)
                                return
                            except requests.exceptions.RequestException as audio_e:
                                logger.warning(f"[{DOMAIN}] Lỗi tải xuống tệp âm thanh (lần thử {audio_attempt + 1}): {audio_e}")
                                time.sleep(0.3)  # Chờ 0.2 giây trước khi thử lại
                        logger.error(f"[{DOMAIN}] Không thể tải xuống âm thanh từ URL sau 3 lần thử.")
                        return
                    else:
                        logger.error(f"[{DOMAIN}] Yêu cầu thất bại với API key %s: %s", api_key, result.get("error_message"))
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 401:
                        logger.warning(f"[{DOMAIN}] Lỗi 401 với API key %s: %s", api_key, e)
                        log_error_key(api_key)
                        break
                    else:
                        logger.warning(f"[{DOMAIN}] Lỗi khi kết nối tới API Zalo (lần thử {attempt + 1}): {e}")
                        time.sleep(0.3)
            logger.error(f"[{DOMAIN}] Tất cả các lần thử kết nối tới API đều thất bại.")
        logger.error(f"[{DOMAIN}] Tất cả các API keys đều không hợp lệ, hết giới hạn miễn phí hoặc gặp lỗi, hãy thử lại vào ngày hôm sau")
    # Đăng ký dịch vụ
    hass.services.register(DOMAIN, 'say', zalo_tts)
    return True
