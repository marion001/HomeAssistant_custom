# encoding: utf-8
import os
import uuid
import logging
import websocket
from datetime import datetime

DOMAIN = 'tts_edge'

CONFIG_id_media_player = 'entity_id'
CONFIG_message = 'message'
TTS_rate = 'rate'
TTS_name = 'name'
TTS_lang = 'lang'

TTS_outputFormat = 'audio-24khz-48kbitrate-mono-mp3'
logger = logging.getLogger(__name__)
current_directory = os.getcwd()
target_directory = os.path.join(current_directory, 'www', DOMAIN)
os.makedirs(target_directory, exist_ok=True)
os.chmod(target_directory, 0o777)

def setup(hass, cfg):
    def process_data(TTS):
        Id_Speak_Hass = TTS.data.get(CONFIG_id_media_player)
        if not Id_Speak_Hass:
            logger.error(f"[{DOMAIN}] Cần nhập id thiết bị phát thông báo")
            return
        if not str(TTS.data.get(CONFIG_message)):
            logger.error(f"[{DOMAIN}] Cần nhập nội dung thông báo {DOMAIN}")
            return

        def calculate_rate(rate_number):
            try:
                rate_number = float(rate_number)
                percentage = (rate_number - 1) * 100
                if percentage > 0:
                    return f"+{int(percentage)}%"
                elif percentage < 0:
                    return f"{int(percentage)}%"
                return "+0%"
            except ValueError:
                logger.error(f"[{DOMAIN}] Lỗi khi tính tỷ lệ rate: {rate_number} không phải là số hợp lệ.")
                return "+0%"

        tts_edge_rate = calculate_rate(str(TTS.data.get(TTS_rate, 1.2)))
        tts_edge_voice_name = str(TTS.data.get(TTS_name, 'vi-VN-HoaiMyNeural'))
        tts_edge_language_code = str(TTS.data.get(TTS_lang, 'vi-VN'))
        request_id = str(uuid.uuid4()).replace('-', '')
        url = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        timestamp = datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT%z (Indochina Time)")
        config_json = f"""
        {{
            "context": {{
                "synthesis": {{
                    "audio": {{
                        "metadataoptions": {{
                            "sentenceBoundaryEnabled": false,
                            "wordBoundaryEnabled": true
                        }},
                        "outputFormat": "{TTS_outputFormat}"
                    }}
                }}
            }}
        }}
        """
        config_headers = (
            f"Content-Type:application/json; charset=utf-8\r\n"
            f"Path:speech.config\r\n"
            f"X-Timestamp:{timestamp}\r\n"
            "\r\n"
        )
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{tts_edge_language_code}">
            <voice name="{tts_edge_voice_name}">
                <prosody pitch='+0Hz' rate='{tts_edge_rate}' volume='+0%'>{str(TTS.data.get(CONFIG_message))}</prosody>
            </voice>
        </speak>
        """
        ssml_headers = (
            f"Content-Type:application/ssml+xml\r\n"
            f"Path:ssml\r\n"
            f"X-RequestId:{request_id}\r\n"
            f"X-Timestamp:{timestamp}\r\n"
            "\r\n"
        )
        try:
            ws = websocket.create_connection(url)
            ws.send(config_headers + config_json)
            ws.send(ssml_headers + ssml_text)
            audio_data = b""
            while True:
                try:
                    message = ws.recv()
                    if isinstance(message, bytes):
                        path_index = message.find(b'Path:audio\r\n')
                        if path_index != -1:
                            audio_dataz = message[path_index + len(b'Path:audio\r\n'):]
                            audio_data += audio_dataz
                    else:
                        if 'Path:turn.end' in message:
                            break
                except Exception as e:
                    logger.error(f"[{DOMAIN}] Đã xảy ra lỗi khi nhận dữ liệu: {e}")
                    return None
        except (websocket.WebSocketConnectionClosedException, websocket.WebSocketBadStatusException) as e:
            logger.error(f"[{DOMAIN}] Lỗi kết nối WebSocket: {e}")
            return None
        except Exception as e:
            logger.error(f"[{DOMAIN}] Lỗi xảy ra: {e}")
            return None
        else:
            if audio_data:
                try:
                    output_file = os.path.join(target_directory, f'{DOMAIN}.mp3')
                    with open(output_file, "wb") as audio_file:
                        audio_file.write(audio_data)
                        logger.info(f"[{DOMAIN}] Đã lưu dữ liệu âm thanh vào tệp: {output_file}")
                        Player_Hass = {
                            'entity_id': Id_Speak_Hass,
                            'media_content_id': f"/local/{DOMAIN}/{DOMAIN}.mp3",
                            'media_content_type': 'music'
                        }
                        hass.services.call('media_player', 'play_media', Player_Hass)
                    return output_file
                except IOError as e:
                    logger.error(f"[{DOMAIN}] Lỗi khi lưu file âm thanh: {e}")
                    return None
            else:
                logger.error(f"[{DOMAIN}] Không có dữ liệu âm thanh để lưu.")
                return None
        finally:
            ws.close()
    # Đăng ký dịch vụ
    hass.services.register(DOMAIN, 'say', process_data)
    return True
