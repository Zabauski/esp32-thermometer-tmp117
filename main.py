# main.py – Comfort + TMP117 + OLED + dual-color LED + active-high buzzer
# main.py – Komfort + TMP117 + OLED + dwukolorowa dioda LED + brzęczyk aktywny w stanie wysokim
from machine import Pin, I2C
import time, struct, ssd1306

# ─────────── settings (ustawienia) ───────────
PIN_SDA_OLED, PIN_SCL_OLED = 21, 22   # OLED I2C pins (Piny I2C dla OLED)
PIN_SDA_TMP,  PIN_SCL_TMP  = 18, 19   # TMP117 I2C pins (Piny I2C dla TMP117)
TMP117_ADDR,  TMP_REG_TEMP = 0x48, 0x00 # TMP117 I2C address and temperature register (Adres I2C TMP117 i rejestr temperatury)

LED_GREEN = Pin(25, Pin.OUT, value=0) # Green LED pin (Pin zielonej diody LED)
LED_RED   = Pin(26, Pin.OUT, value=0) # Red LED pin (Pin czerwonej diody LED)
BUZZER    = Pin(15, Pin.OUT, value=0) # active-high buzzer pin (Pin brzęczyka aktywowanego stanem wysokim)

T_MIN_OK, T_MAX_OK = 20.0, 26.0       # Comfortable temperature range in °C (Komfortowy zakres temperatur w °C)

# ─────────── peripherals (urządzenia peryferyjne) ───────────
i2c_oled = I2C(0, scl=Pin(PIN_SCL_OLED), sda=Pin(PIN_SDA_OLED), freq=400_000) # Initialize I2C for OLED display (Inicjalizacja I2C dla wyświetlacza OLED)
i2c_tmp  = I2C(1, scl=Pin(PIN_SCL_TMP),  sda=Pin(PIN_SDA_TMP),  freq=400_000) # Initialize I2C for TMP117 sensor (Inicjalizacja I2C dla czujnika TMP117)
oled = ssd1306.SSD1306_I2C(128, 64, i2c_oled) # Initialize OLED display (Inicjalizacja wyświetlacza OLED)

# ─────────── functions (funkcje) ───────────
def read_tmp117():
    # Function to read temperature from TMP117 (Funkcja do odczytu temperatury z TMP117)
    raw = i2c_tmp.readfrom_mem(TMP117_ADDR, TMP_REG_TEMP, 2) # Read 2 bytes from the temperature register (Odczytaj 2 bajty z rejestru temperatury)
    (val,) = struct.unpack(">h", raw)    # Unpack raw bytes into a signed short (big-endian) (Rozpakuj surowe bajty na liczbę całkowitą ze znakiem (big-endian))
    return val * 0.0078125               # Convert to degrees Celsius (1 LSB = 1/128 °C) (Konwertuj na stopnie Celsjusza (1 LSB = 1/128 °C))

def beep(ms=150):
    # Function for a short beep (Funkcja generująca krótki sygnał dźwiękowy)
    BUZZER.value(1)                      # Turn the buzzer on (Włącz brzęczyk)
    time.sleep_ms(ms)                    # Wait for a specified duration in milliseconds (Poczekaj przez określony czas w milisekundach)
    BUZZER.value(0)                      # Turn the buzzer off (Wyłącz brzęczyk)

def show(temp, ok):
    # Function to display data on OLED (Funkcja do wyświetlania danych na OLED)
    oled.fill(0)                         # Clear the display (Wyczyść wyświetlacz)
    oled.text("Temp: {:.2f}C".format(temp), 0, 16) # Display the temperature (Wyświetl temperaturę)
    oled.text("Status: {}".format("NORM" if ok else "BAD!"), 0, 32) # Display the status (Wyświetl status)
    oled.show()                          # Update the display (Zaktualizuj wyświetlacz)

# ─────────── startup screen (ekran startowy) ───────────
oled.fill(0)
oled.text("Comfort Monitor",  0, 0)
oled.text("TMP117 addr 0x48", 0, 10)
oled.show()

# ─────────── main loop (pętla główna) ───────────
prev_ok = True # Variable to store the previous status (Zmienna do przechowywania poprzedniego stanu)
while True:
    try:
        # Error handling block for sensor reading (Blok obsługi błędów dla odczytu z czujnika)
        t = read_tmp117()
        ok = T_MIN_OK <= t <= T_MAX_OK   # Check if temperature is within the comfortable range (Sprawdź, czy temperatura mieści się w komfortowym zakresie)
    except OSError as e:
        # Catch potential I2C communication errors (Przechwyć potencjalne błędy komunikacji I2C)
        LED_GREEN.off(); LED_RED.on()     # Turn green LED off, red LED on (Wyłącz zieloną diodę, włącz czerwoną)
        oled.fill(0); oled.text("TMP117 ERROR", 0, 24); oled.show() # Display error on OLED (Wyświetl błąd na OLED)
        beep(400)                        # Make a long beep (Wygeneruj długi sygnał dźwiękowy)
        time.sleep(2)                    # Wait for 2 seconds (Poczekaj 2 sekundy)
        continue                         # Skip the rest of the loop and start over (Pomiń resztę pętli i zacznij od nowa)

    # LED signaling (Sygnalizacja LED)
    LED_GREEN.value(ok)                  # Green LED is on if temperature is OK (Zielona dioda świeci, jeśli temperatura jest w normie)
    LED_RED.value(not ok)                # Red LED is on if temperature is not OK (Czerwona dioda świeci, jeśli temperatura jest poza normą)

    # Sound alarm (beeps constantly if red LED is on) (Alarm dźwiękowy (ciągły sygnał, gdy świeci czerwona dioda))
    BUZZER.value(ok)                     # Turn on the buzzer based on the 'ok' status (Włącz brzęczyk w oparciu o status 'ok')

    # OLED Display (Wyświetlacz OLED)
    show(t, ok)                          # Show data on the display (Pokaż dane na wyświetlaczu)
    time.sleep(1)                        # Wait for 1 second before the next reading (Poczekaj 1 sekundę przed następnym odczytem)
