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

      input_number: 
        tts_zalo_speed:
          name: TTS Zalo Speed
          icon: mdi:speedometer
          min: 0.8
          max: 1.2
          step: 0.1


 - Cấu Hình File <b>input_text.yaml</b> (Nội dung văn bản cần phát thông báo)
 
        tts_input_text:
          name: "Nhập Nội Dung"

- Cấu Hình File <b>input_number.yaml</b> (Nội dung văn bản cần phát thông báo)

        tts_zalo_speaker_id:
          name: Giọng đọc TTS Zalo
          options:
            - Nữ (Miền Nam)
            - Nữ (Miền Bắc)
            - Nam (Miền Nam)
            - Nam (Miền Bắc)
          initial: Nữ (Miền Nam)
          icon: mdi:account-voice
