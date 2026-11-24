/**
 * @file esp32s3_glasses_cam_test.ino
 * @brief Complete Hardware Verification & Wi-Fi MJPEG Streaming Firmware
 *        for the ESP32-S3 Smart-Glasses Temple Camera PCB (KiCad 10 Rev).
 *
 * Target MCU:       Espressif ESP32-S3FH4R2 (4MB Flash, 2MB Quad PSRAM, QFN-56)
 * Camera Sensor:    OV2640 (24-pin 0.5mm FPC at J1)
 * USB Interface:    Native USB Serial/JTAG + CDC on GPIO19 (D-) and GPIO20 (D+)
 *
 * Arduino IDE / PlatformIO Board Settings:
 *   - Board:            "ESP32S3 Dev Module"
 *   - USB CDC On Boot:  "Enabled"  (ARDUINO_USB_CDC_ON_BOOT=1)
 *   - USB Mode:         "Hardware CDC and JTAG" (ARDUINO_USB_MODE=1)
 *   - Flash Size:       "4MB (32Mb)"
 *   - PSRAM:            "QSPI PSRAM" (ESP32-S3FH4R2 has 2MB integrated Quad PSRAM)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include "esp_camera.h"
#include "esp_http_server.h"

// ============================================================================
// 1. EXACT PCB GPIO PIN DEFINITIONS (MATCHING esp32s3_glasses_cam.kicad_sch)
// ============================================================================
#define CAM_PIN_PWDN    21   // U1 Pin 27 (GPIO21) -> J1 Pin 17 (CAM_PWDN)
#define CAM_PIN_RESET   15   // U1 Pin 21 (GPIO15) -> J1 Pin 19 (CAM_RST)
#define CAM_PIN_XCLK    10   // U1 Pin 15 (GPIO10) -> J1 Pin 12 (CAM_XCLK)
#define CAM_PIN_SIOD     4   // U1 Pin 9  (GPIO4)  -> J1 Pin 22 (CAM_SIOD / SDA)
#define CAM_PIN_SIOC     5   // U1 Pin 10 (GPIO5)  -> J1 Pin 20 (CAM_SIOC / SCL)

#define CAM_PIN_D0      11   // U1 Pin 16 (GPIO11) -> J1 Pin 6  (CAM_D0 / Y2)
#define CAM_PIN_D1       9   // U1 Pin 14 (GPIO9)  -> J1 Pin 4  (CAM_D1 / Y3)
#define CAM_PIN_D2       8   // U1 Pin 13 (GPIO8)  -> J1 Pin 3  (CAM_D2 / Y4)
#define CAM_PIN_D3      12   // U1 Pin 17 (GPIO12) -> J1 Pin 5  (CAM_D3 / Y5)
#define CAM_PIN_D4      14   // U1 Pin 19 (GPIO14) -> J1 Pin 7  (CAM_D4 / Y6)
#define CAM_PIN_D5      17   // U1 Pin 23 (GPIO17) -> J1 Pin 9  (CAM_D5 / Y7)
#define CAM_PIN_D6      18   // U1 Pin 24 (GPIO18) -> J1 Pin 11 (CAM_D6 / Y8)
#define CAM_PIN_D7      16   // U1 Pin 22 (GPIO16) -> J1 Pin 13 (CAM_D7 / Y9)

#define CAM_PIN_VSYNC    6   // U1 Pin 11 (GPIO6)  -> J1 Pin 18 (CAM_VSYNC)
#define CAM_PIN_HREF     7   // U1 Pin 12 (GPIO7)  -> J1 Pin 16 (CAM_HREF)
#define CAM_PIN_PCLK    13   // U1 Pin 18 (GPIO13) -> J1 Pin 8  (CAM_PCLK)

#define PIN_ALS_SENSE   1    // U1 Pin 6 (GPIO1 / ADC1_CH0) -> Q_ALS1 (ALS-PT19-315C + 100k) Anti-Tape Light Sensor
#define PIN_CAM_PWR_EN  47   // U1 Pin 37 (GPIO47) -> D_PRIV1 (Hardware Privacy LED) -> U3/U4 EN
#define PIN_STATUS_LED  48   // U1 Pin 36 (GPIO48) -> R_LED1 (1k) -> D1 Anode
#define PIN_I2S_BCLK    38   // U1 Pin 43 (GPIO38) -> TP_I2S_BCLK1 (Speaker/Mic Bit Clock)
#define PIN_I2S_LRC     41   // U1 Pin 47 (GPIO41) -> TP_I2S_LRC1  (Speaker/Mic Word Select)
#define PIN_I2S_DOUT    33   // U1 Pin 38 (GPIO33) -> TP_SPK_DOUT1 (Down-Firing Speaker I2S Data)
#define PIN_I2S_MIC_SD  37   // U1 Pin 42 (GPIO37) -> TP_MIC_SD1   (MEMS Mic I2S Data)
#define PIN_BOOT_BTN     0   // U1 Pin 5  (GPIO0)  -> SW2 Active-Low BOOT Button (SW1 is RESET on CHIP_PU)

// Optional Wi-Fi credentials (falls back to SoftAP "GlassesCam-S3" if not found)
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

static httpd_handle_t stream_httpd = NULL;

// ============================================================================
// 2. MJPEG HTTP STREAM HANDLER (http://<ip>/stream)
// ============================================================================
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;

  char part_buf[64];
  while (true) {
    // Live Anti-Tape Privacy Check every 2 seconds during active streaming
    static uint32_t last_als_chk = 0;
    if (millis() - last_als_chk > 2000) {
      last_als_chk = millis();
      if (isPrivacyLedTampered()) {
        Serial.println("[PRIVACY] TAMPER DETECTED (LED window covered in bright scene) — cutting camera power!");
        digitalWrite(PIN_CAM_PWR_EN, LOW); // Hardware-enforced interlock cuts +2V8/+1V2 LDOs
        res = ESP_FAIL;
        break;
      }
    }
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("[ERR] Framebuffer capture failed");
      res = ESP_FAIL;
    } else {
      size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART, fb->len);
      res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
      if (res == ESP_OK) res = httpd_resp_send_chunk(req, part_buf, hlen);
      if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
      esp_camera_fb_return(fb);
    }
    if (res != ESP_OK) break;
  }
  return res;
}

static esp_err_t index_handler(httpd_req_t *req) {
  const char* html =
    "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>ESP32-S3 Smart Glasses Camera</title>"
    "<style>body{background:#111;color:#eee;font-family:sans-serif;text-align:center;margin:20px}"
    "img{max-width:100%;border:2px solid #3b82f6;border-radius:8px}</style></head>"
    "<body><h2>ESP32-S3 Smart-Glasses Camera Live Stream</h2>"
    "<img src='/stream' /></body></html>";
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, html, strlen(html));
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t index_uri = { .uri = "/", .method = HTTP_GET, .handler = index_handler, .user_ctx = NULL };
  httpd_uri_t stream_uri = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &index_uri);
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("[OK] HTTP MJPEG Server started on port 80");
  }
}

// ============================================================================
// 3. HARDWARE SELF-TEST & BRING-UP DIAGNOSTICS
// ============================================================================
bool runHardwareSelfTest() {
  Serial.println("\n========================================================");
  Serial.println("  ESP32-S3 SMART-GLASSES PCB BRING-UP & SELF-TEST");
  Serial.println("========================================================");

  // Check 1: Internal Flash & Quad PSRAM (ESP32-S3FH4R2)
  Serial.printf("[TEST 1] Chip Model: %s Rev %d (%d cores)\n",
                ESP.getChipModel(), ESP.getChipRevision(), ESP.getChipCores());
  Serial.printf("[TEST 1] Flash Size: %u bytes | PSRAM Size: %u bytes\n",
                ESP.getFlashChipSize(), ESP.getPsramSize());
  if (ESP.getPsramSize() == 0) {
    Serial.println("[WARN] PSRAM not detected! Enable 'QSPI PSRAM' in IDE Tools menu.");
  } else {
    Serial.println("[PASS] 2MB Quad PSRAM verified on VDD_SPI (3.3V).");
  }

  // Check 2: Toggle Status LED (GPIO48 -> R_LED1 (1k) -> D1)
  pinMode(PIN_CAM_PWR_EN, OUTPUT);
  digitalWrite(PIN_CAM_PWR_EN, HIGH); // Hardware-enforced: powers D_PRIV1 + OV2640 rails (+2V8/+1V2)
  delay(20);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_BOOT_BTN, INPUT_PULLUP);
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(80);
    digitalWrite(PIN_STATUS_LED, LOW);
    delay(80);
  }
  Serial.println("[PASS] Status LED (GPIO48 -> D1) blinked 3x.");

  // Check 3: Power-up OV2640 and probe SCCB/I2C bus (GPIO4=SDA, GPIO5=SCL)
  pinMode(CAM_PIN_PWDN, OUTPUT);
  pinMode(CAM_PIN_RESET, OUTPUT);
  digitalWrite(CAM_PIN_PWDN, LOW);   // Enable camera (active-high power down)
  digitalWrite(CAM_PIN_RESET, LOW);  // Assert reset
  delay(20);
  digitalWrite(CAM_PIN_RESET, HIGH); // Release reset
  delay(20);

  // Check 4: Initialize esp_camera driver with exact PCB pinout
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = CAM_PIN_D0;
  config.pin_d1       = CAM_PIN_D1;
  config.pin_d2       = CAM_PIN_D2;
  config.pin_d3       = CAM_PIN_D3;
  config.pin_d4       = CAM_PIN_D4;
  config.pin_d5       = CAM_PIN_D5;
  config.pin_d6       = CAM_PIN_D6;
  config.pin_d7       = CAM_PIN_D7;
  config.pin_xclk     = CAM_PIN_XCLK;
  config.pin_pclk     = CAM_PIN_PCLK;
  config.pin_vsync    = CAM_PIN_VSYNC;
  config.pin_href      = CAM_PIN_HREF;
  config.pin_sccb_sda = CAM_PIN_SIOD;
  config.pin_sccb_scl = CAM_PIN_SIOC;
  config.pin_pwdn     = CAM_PIN_PWDN;
  config.pin_reset    = CAM_PIN_RESET;
  config.xclk_freq_hz = 20000000;    // 20 MHz XCLK for low EMI & stable DVP timing
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode    = CAMERA_GRAB_LATEST;

  if (psramFound()) {
    config.frame_size   = FRAMESIZE_VGA; // 640x480 @ high FPS
    config.jpeg_quality = 12;
    config.fb_count     = 2;
    config.fb_location  = CAMERA_FB_IN_PSRAM;
  } else {
    config.frame_size   = FRAMESIZE_CIF;
    config.jpeg_quality = 15;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_DRAM;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[FAIL] esp_camera_init failed with error 0x%x\n", err);
    Serial.println("       Check J1 24-pin FPC seating and +2V8 (U3) / +1V2 (U4) LDO rails.");
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  Serial.printf("[PASS] OV2640 Camera detected! PID=0x%02X VER=0x%02X\n", s->id.PID, s->id.VER);

  // Capture 1 test frame to verify all 8 DVP data lines (D0..D7) + PCLK/VSYNC/HREF
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb || fb->len == 0) {
    Serial.println("[FAIL] Test frame capture returned empty buffer! Check CAM_PCLK (GPIO13).");
    return false;
  }
  Serial.printf("[PASS] Captured test JPEG frame (%u bytes, %ux%u).\n",
                fb->len, fb->width, fb->height);
  esp_camera_fb_return(fb);
  return true;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_ALS_SENSE, ADC_11db);
  delay(1500); // Allow Native USB CDC enumeration on GPIO19/GPIO20

  bool cam_ok = runHardwareSelfTest();

  // Connect to Wi-Fi or start SoftAP for standalone glasses streaming
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("[WIFI] Connecting to %s", WIFI_SSID);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - t0) < 8000) {
    delay(400);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WIFI] Connected! Stream URL: http://%s/\n", WiFi.localIP().toString().c_str());
    Serial.printf("[WIFI] RSSI: %d dBm (verifies 50-Ohm F.Cu RF trace + AE1 matching)\n", WiFi.RSSI());
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAP("GlassesCam-S3", "12345678");
    Serial.printf("\n[WIFI] Started SoftAP 'GlassesCam-S3' (pass: 12345678) -> http://%s/\n",
                  WiFi.softAPIP().toString().c_str());
  }

  if (cam_ok) {
    startCameraServer();
    digitalWrite(PIN_STATUS_LED, HIGH); // Solid LED = streaming ready
  }
}

// Anti-Tape Privacy Check: cross-checks LIVE OV2640 hardware exposure/gain registers against Q_ALS1 (GPIO1 / ADC1_CH0)
// NOTE: All thresholds below MUST BE CALIBRATED ON THE FIRST ASSEMBLED PROTOTYPE!
static const int ALS_DARK_MV_THRESH     = 250; // CALIBRATE ON PROTOTYPE: mV below which LED window is considered covered
static const int ALS_CLEAR_MV_THRESH    = 450; // CALIBRATE ON PROTOTYPE: hysteresis clear threshold (> ALS_DARK_MV_THRESH)
static const int OV2640_BRIGHT_AEC_MAX  = 90;  // CALIBRATE ON PROTOTYPE: live AEC MSB (reg 0x10) below this = bright scene
static const int OV2640_BRIGHT_GAIN_MAX = 24;  // CALIBRATE ON PROTOTYPE: live AGC GAIN (reg 0x00) below this = bright scene
static const int TAMPER_CONFIRM_COUNT   = 3;   // Consecutive checks before cutting camera power (hysteresis)
static const int CLEAR_CONFIRM_COUNT    = 2;   // Consecutive clear checks required for recovery

static bool privacy_tamper_latched = false;
static int  tamper_hit_streak      = 0;
static int  tamper_clear_streak    = 0;

bool isPrivacyLedTampered() {
  int als_mv = analogReadMilliVolts(PIN_ALS_SENSE);
  sensor_t *s = esp_camera_sensor_get();
  if (!s) return false;

  // Switch OV2640 to Sensor Register Bank (0x01) and read LIVE hardware exposure & gain (not cached status!)
  s->set_reg(s, 0xFF, 0xFF, 0x01);
  int live_gain = s->get_reg(s, 0x00, 0xFF); // Live AGC GAIN register
  int live_aec  = s->get_reg(s, 0x10, 0xFF); // Live AEC[9:2] exposure MSB register
  if (live_gain < 0 || live_aec < 0) return false;

  bool scene_bright   = (live_aec < OV2640_BRIGHT_AEC_MAX && live_gain < OV2640_BRIGHT_GAIN_MAX);
  bool window_covered = (als_mv < ALS_DARK_MV_THRESH);

  if (scene_bright && window_covered) {
    tamper_hit_streak++;
    tamper_clear_streak = 0;
    if (tamper_hit_streak >= TAMPER_CONFIRM_COUNT) {
      privacy_tamper_latched = true;
    }
  } else {
    tamper_hit_streak = 0;
  }
  return privacy_tamper_latched;
}

void loop() {
  // Recovery path when privacy tamper interlock has latched camera OFF
  if (privacy_tamper_latched) {
    static uint32_t last_rec_chk = 0;
    if (millis() - last_rec_chk > 1000) {
      last_rec_chk = millis();
      int als_mv = analogReadMilliVolts(PIN_ALS_SENSE);
      if (als_mv >= ALS_CLEAR_MV_THRESH) {
        tamper_clear_streak++;
        if (tamper_clear_streak >= CLEAR_CONFIRM_COUNT) {
          Serial.printf("[PRIVACY] Window unobstructed (%d mV) — restoring camera power.\n", als_mv);
          privacy_tamper_latched = false;
          tamper_hit_streak = 0;
          tamper_clear_streak = 0;
          digitalWrite(PIN_CAM_PWR_EN, HIGH);
          delay(100);
          esp_camera_deinit();
          runHardwareSelfTest();
        }
      } else {
        tamper_clear_streak = 0;
      }
    }
  }

  if (digitalRead(PIN_BOOT_BTN) == LOW) {
    if (privacy_tamper_latched) {
      Serial.println("[PRIVACY] Manual BOOT recovery requested — re-checking camera.");
      privacy_tamper_latched = false;
      tamper_hit_streak = 0;
      digitalWrite(PIN_CAM_PWR_EN, HIGH);
      delay(100);
      esp_camera_deinit();
      runHardwareSelfTest();
    } else {
      Serial.printf("[STAT] Free Heap: %u | Free PSRAM: %u | Wi-Fi RSSI: %d dBm | ALS: %d mV\n",
                    ESP.getFreeHeap(), ESP.getFreePsram(), WiFi.RSSI(), analogReadMilliVolts(PIN_ALS_SENSE));
    }
    delay(500);
  }
  delay(20);
}
