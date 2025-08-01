import serial
import time

def calc_bcc(data: bytes) -> int:
    """BCC (Block Check Character) hesaplar."""
    bcc = 0
    for b in data:
        bcc ^= b
    return bcc

# --- Seri port ayarları (başlangıçta 300 baud)
ser = serial.Serial(
    port="/dev/ttyUSB0",  # veya COM3 (Windows)
    baudrate=300,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=2
)

def send_and_recv(cmd: bytes, wait=1.0):
    ser.write(cmd)
    time.sleep(wait)
    return ser.read(ser.in_waiting or 1)

# --- 1. Oturum başlatma: cihaz kimliği iste
print("Cihaz kimliği isteniyor...")
response = send_and_recv(b"/?!\r\n", wait=1.5)
print("Cihazdan gelen:", response)

# --- 2. Baud hızı artır: örneğin 9600bps → 5 = 9600
# Yanıt geldiğinde: örnek /SAT6EM72000656621\r\n
if b"/" in response:
    time.sleep(0.5)
    send_and_recv(b"\x06" + b"050\r\n")  # ACK + baudrate (5:9600)
    ser.baudrate = 9600
    time.sleep(0.5)

    # --- 3. 1.8.0 (toplam aktif enerji) iste
    # Veri yapısı: SOH R2 STX 1.8.0() ETX BCC
    soh = b'\x01'
    stx = b'\x02'
    etx = b'\x03'
    cmd = b'R2' + stx + b'1.8.0()\x03'
    bcc = bytes([calc_bcc(cmd)])  # STX'ten ETX'e kadar olan veri
    request = soh + cmd + bcc

    print("Enerji endeksi isteniyor...")
    response = send_and_recv(request, wait=2.0)
    print("Gelen veri:", response)

    # --- 4. Yanıtı ayıkla
    try:
        start = response.find(b'1.8.0(') + len(b'1.8.0(')
        end = response.find(b'*kWh')
        value = response[start:end].decode()
        print(f"Toplam Aktif Enerji: {value} kWh")
    except Exception as e:
        print("Veri ayıklama hatası:", e)
else:
    print("Sayaçtan geçerli yanıt alınamadı.")
