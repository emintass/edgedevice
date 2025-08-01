import serial

ser = serial.Serial(
    port='/dev/ttyUSB0',  # adaptörün portu
    baudrate=300,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=2.0
)

try:
    ser.write(b'/?!\r\n')   # Örnek: sayaç kimlik sorgu komutu
    response = ser.readline()
    print("Received:", response.decode(errors='ignore'))

finally:
    ser.close()
