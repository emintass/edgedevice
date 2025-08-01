import serial

ser = serial.Serial(
    port='/dev/ttyUSB0',  # adaptörün portu
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

try:
    ser.write(b'/?!\r\n')   # Örnek: sayaç kimlik sorgu komutu
    response = ser.readline()
    print("Received:", response.decode(errors='ignore'))

finally:
    ser.close()
