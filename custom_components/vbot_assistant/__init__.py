import requests
import json
import logging
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_PLAYING, STATE_IDLE, STATE_PAUSED

# Cấu hình logger
_LOGGER = logging.getLogger(__name__)

VBOT_ASSISTANT = "Vbot Assistant"
API_URL = None

def setup(hass: HomeAssistant, config: dict):
    """Khởi tạo Vbot Assistant và các dịch vụ"""
    global API_URL

    # Đọc URL API từ cấu hình trong configuration.yaml
    API_URL = config.get("vbot_assistant", {}).get("api_url")

    # Kiểm tra và thông báo lỗi nếu không có API_URL cấu hình
    if not API_URL:
        _LOGGER.error(f"[{VBOT_ASSISTANT}] Tham số api_url chưa được cấu hình trong configuration.yaml. Dừng việc khởi tạo custom_components: vbot_assistant")
        return False

    #Khởi tạo dịch vụ media_control
    def vbot_media_control(call):
        #Lấy action từ dữ liệu yêu cầu, mặc định là 'play'
        action = str(call.data.get("action", "play")).lower
        # Các tham số chỉ cần thiết khi action là 'play'
        media_link = str(call.data.get("media_link"))
        media_name = str(call.data.get("media_name", ""))
        media_cover = str(call.data.get("media_cover", ""))
        media_player_source = str(call.data.get("media_player_source", "Home Assistant"))
        # Kiểm tra nếu action là 'play' và yêu cầu các tham số media
        if action == "play" and not media_link:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Không có link/url liên kết media_link được cung cấp.")
            return False
        # Xác định action (play, pause, stop, resume)
        if action not in ["play", "pause", "stop", "resume"]:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Tham số action không hợp lệ: {action}")
            return False
        # Tạo payload
        payload_data = {
            "type": 1,
            "data": "media_control",
            "action": action
        }
        # Chỉ thêm các trường nếu action là 'play'
        if action == "play":
            payload_data.update({
                "media_link": media_link,
                "media_name": media_name,
                "media_cover": media_cover,
                "media_player_source": media_player_source
            })
        payload = json.dumps(payload_data)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
            if response.status_code == 200:
                # Kiểm tra dữ liệu trả về JSON để xác định thành công
                try:
                    response_data = response.json()
                    #kiểm tra dữ liệu trả về "success"
                    if response_data.get("success") == True:
                        _LOGGER.info(f"[{VBOT_ASSISTANT}] {response_data.get('message')}")
                        # Cập nhật trạng thái media player theo action
                        if action == "play":
                            hass.states.set("media_player.vbot_assistant", STATE_PLAYING, response_data)
                        elif action == "pause":
                            hass.states.set("media_player.vbot_assistant", STATE_PAUSED, response_data)
                        elif action == "stop":
                            hass.states.set("media_player.vbot_assistant", STATE_IDLE, response_data)
                        elif action == "resume":
                            hass.states.set("media_player.vbot_assistant", STATE_PLAYING, response_data)
                    else:
                        _LOGGER.error(f"[{VBOT_ASSISTANT}] {response_data.get('message')}")
                        hass.states.set("media_player.vbot_assistant", STATE_IDLE, response_data)
                except ValueError:
                    _LOGGER.error(f"[{VBOT_ASSISTANT}] Dữ liệu trả về không phải JSON.")
            else:
                _LOGGER.error(f"[{VBOT_ASSISTANT}] Yêu cầu API không thành công, mã lỗi: {response.status_code}")
                hass.states.set("media_player.vbot_assistant", STATE_IDLE, response_data)
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Lỗi khi gửi yêu cầu API: {e}")
            hass.states.set("media_player.vbot_assistant", STATE_IDLE)

    #Khởi tạo dịch vụ TTS
    def vbot_tts(call):
        message = str(call.data.get("message"))
        if not message:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Không có nội dung văn bản để phát TTS")
            return False
        payload_data = {
            "type": 3,
            "data": "tts",
            "action": "notify",
            "value": message
        }
        payload = json.dumps(payload_data)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("success") == True:
                        _LOGGER.info(f"[{VBOT_ASSISTANT}] {response_data.get('message')}: ({message})")
                    else:
                        _LOGGER.error(f"[{VBOT_ASSISTANT}] {response_data.get('message')}: ({message})")
                    hass.states.set("vbot_assistant.volume", "VBot Text To Speak", response_data)
                except ValueError:
                    _LOGGER.error(f"[{VBOT_ASSISTANT}] Dữ liệu trả về không phải JSON")
            else:
                _LOGGER.error(f"[{VBOT_ASSISTANT}] Phát TTS thất bại, mã lỗi: {response.status_code}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Lỗi khi gửi yêu cầu phát TTS: {e}")

    #Khởi tạo dịch vụ volume
    def vbot_volume(call):
        action = str(call.data.get("action")).lower
        if action not in ["setup", "up", "down", "min", "max"]:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Tham số action không hợp lệ: {action}")
            return False
        payload_data = {
            "type": 2,
            "data": "volume",
            "action": action
        }
        # Chỉ thêm các trường nếu action là 'setup'
        if action == "setup":
            value = int(call.data.get("value"))
            # Kiểm tra xem giá trị value có tồn tại và nằm trong khoảng 0-100
            if value is None or not (0 <= int(value) <= 100):
                _LOGGER.error(f"[{VBOT_ASSISTANT}] Thiếu hoặc giá trị không hợp lệ cho tham số value: (0->100)")
                return False
            payload_data.update({
                "value": value
            })
        payload = json.dumps(payload_data)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("success") == True:
                        _LOGGER.info(f"[{VBOT_ASSISTANT}] {response_data.get('message')}: ({response_data.get('volume')})")
                    else:
                        _LOGGER.error(f"[{VBOT_ASSISTANT}] {response_data.get('message')}: ({response_data.get('volume')})")
                    hass.states.set("vbot_assistant.volume", "VBot Volume", response_data)
                except ValueError:
                    _LOGGER.error(f"[{VBOT_ASSISTANT}] Dữ liệu trả về không phải JSON")
            else:
                _LOGGER.error(f"[{VBOT_ASSISTANT}] Thay đổi âm lượng thất bại, mã lỗi: {response.status_code}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Lỗi khi gửi yêu cầu thay đổi âm lượng: {e}")


    #Khởi tạo dịch vụ chatbot
    def vbot_chatbot(call):
        message = str(call.data.get("message"))
        if not message:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Không có nội dung văn bản message")
            return False
        payload_data = {
            "type": 3,
            "data": "main_processing",
            "action": "processing_api",
            "value": message
        }

        payload = json.dumps(payload_data)
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(API_URL, headers=headers, data=payload)
            response.raise_for_status()
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("success") == True:
                        _LOGGER.info(f"[{VBOT_ASSISTANT}] {response_data.get('text_input')}: {response_data.get('message')}")
                    else:
                        _LOGGER.error(f"[{VBOT_ASSISTANT}] {response_data.get('text_input')}: {response_data.get('message')}")
                    hass.states.set("vbot_assistant.chatbot", "VBot ChatBot", response_data)
                except ValueError:
                    _LOGGER.error(f"[{VBOT_ASSISTANT}] Dữ liệu trả về không phải JSON")
            else:
                _LOGGER.error(f"[{VBOT_ASSISTANT}] Có lỗi xảy ra, mã lỗi: {response.status_code}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"[{VBOT_ASSISTANT}] Lỗi khi gửi yêu cầu: {e}")


    # Đăng ký các dịch vụ vào Home Assistant
    hass.services.register("vbot_assistant", "media_control", vbot_media_control)
    hass.states.set("media_player.vbot_assistant", STATE_IDLE, {"icon": "mdi:multimedia"})
    _LOGGER.info(f"[{VBOT_ASSISTANT}] Dịch vụ vbot_assistant.media_control đã được khởi tạo trong Home Assistant thành công")


    hass.services.register("vbot_assistant", "tts", vbot_tts)
    hass.states.set("vbot_assistant.tts", "VBot Text To Speak", {"icon": "mdi:account-voice"})
    _LOGGER.info(f"[{VBOT_ASSISTANT}] Dịch vụ vbot_assistant.tts đã được khởi tạo trong Home Assistant thành công")


    hass.services.register("vbot_assistant", "chatbot", vbot_chatbot)
    hass.states.set("vbot_assistant.chatbot", "VBot ChatBot", {"icon": "mdi:robot-outline"})
    _LOGGER.info(f"[{VBOT_ASSISTANT}] Dịch vụ vbot_assistant.chatbot đã được khởi tạo trong Home Assistant thành công")

    hass.services.register("vbot_assistant", "volume", vbot_volume)
    hass.states.set("vbot_assistant.volume", "VBot Volume", {"icon": "mdi:volume-high"})
    _LOGGER.info(f"[{VBOT_ASSISTANT}] Dịch vụ vbot_assistant.vbot_volume đã được khởi tạo trong Home Assistant thành công")

    return True
