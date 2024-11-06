TTS Zalo: Chuyển văn bản thành giọng nói của Zalo

- Cần sao chép thư mục <b>tts_zalo</b> vào trong thư mục <b>custom_components</b> sẽ có đường dẫn dạng: <b>"custom_components/tts_zalo"</b>


- Cấu Hình File <b>configuration.yaml</b>
  - nếu có nhiều key sẽ thêm thành nhiều dòng
    
        tts_zalo:
          apikey:
            - '645g645g654g6546456ggtv43g4'
            - '888888888888888888888888888'
            - '99999999999999999999999999'
- Cấu Hình File <b>input_number.yaml</b> (Chỉnh tốc độ đọc)


        tts_zalo_speed:
          name: TTS Zalo Speed
          icon: mdi:speedometer
          min: 0.8
          max: 1.2
          step: 0.1
          initial: 0.9


 - Cấu Hình File <b>input_text.yaml</b> (Nội dung văn bản cần phát thông báo)
 
        tts_input_text:
          name: "Nhập Nội Dung"

- Cấu Hình File <b>input_select.yaml</b> (Chọn giọng đọc vả chọn thiết bị phát thông báo, cần thay các media_player.xxxxxxx tương ứng với các thiết bị của bạn)

        tts_zalo_speaker_id:
          name: Giọng đọc TTS Zalo
          options:
            - Nữ (Miền Nam)
            - Nữ (Miền Bắc)
            - Nam (Miền Nam)
            - Nam (Miền Bắc)
          initial: Nữ (Miền Nam)
          icon: mdi:account-voice

        tts_media_player_speaker:
          name: Chọn thiết bị phát thông báo
          options:
            - media_player.esp32_media_speaker_player
            - media_player.googlehome
            - media_player.googlehome_mini
          initial: media_player.esp32_media_speaker_player


- Cấu Hình File <b>scripts.yaml</b> (Thực thi chuyển đổi và phát thông báo tts)
  
        zalo_text_to_speak:
          sequence:  
          - service: tts_zalo.say
            data_template:
              entity_id: "{{ states('input_select.tts_media_player_speaker') }}"
              message: '{{ states("input_text.tts_input_text") }}'
              speed: '{{ states("input_number.tts_zalo_speed") }}'
              speaker_id: >
                {% if states("input_select.tts_zalo_speaker_id") == "Nữ (Miền Nam)" %}
                  1
                {% elif states("input_select.tts_zalo_speaker_id") == "Nữ (Miền Bắc)" %}
                  2
                {% elif states("input_select.tts_zalo_speaker_id") == "Nam (Miền Nam)" %}
                  3
                {% elif states("input_select.tts_zalo_speaker_id") == "Nam (Miền Bắc)" %}
                  4
                {% else %}
                  1
                {% endif %}

- Cấu hình entities <b>ui lovelace</b>

        type: entities
        entities:
          - entity: input_text.tts_input_text
            name: Nhập nội dung phát thông báo
          - entity: input_select.tts_media_player_speaker
            icon: mdi:speaker-wireless
          - entity: input_select.tts_zalo_speaker_id
            name: Giọng Đọc
          - entity: input_number.tts_zalo_speed
            name: Tốc Độ Đọc
          - entity: script.zalo_text_to_speak
            icon: mdi:send-check-outline
            name: "Phát Thông Báo:"
        state_color: true
        title: Phát Thông Báo TTS Zalo

