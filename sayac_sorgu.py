import serial
import time


ser = serial.Serial(
    port='/dev/ttyUSB0',  # adaptörün portu
    baudrate=300,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=2.0
)

try:
    for i in range(10):
    
        ser.write(b'/?!\r\n')   # Örnek: sayaç kimlik sorgu komutu
        response = ser.readline()
        response2 = ser.readline()
        print("Received:", response.decode(errors='ignore'))
        print("Received:", response2.decode(errors='ignore'))
        time.sleep(5)




try:
    for i in range(10):
    
        ser.write(b'/?!\r\n')   # Örnek: sayaç kimlik sorgu komutu
        response = ser.readline()
        response2 = ser.readline()
        print("Received:", response.decode(errors='ignore'))
        print("Received:", response2.decode(errors='ignore'))
    
finally:
    ser.close()