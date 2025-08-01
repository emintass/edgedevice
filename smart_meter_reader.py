# app.py
from flask import Flask, jsonify
import serial
import time
from binascii import hexlify
import threading
import queue
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__)
meter_data_queue = queue.Queue(maxsize=1)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

class IEC62056Reader:
    # control chars
    SOH = 0x01  # header start
    STX = 0x02  # text start
    ETX = 0x03  # text end
    ACK = 0x06

    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.ser = None

        self.baud_rates = {
            '0': 300, '1': 600, '2': 1200, '3': 2400,
            '4': 4800, '5': 9600, '6': 19200
        }


    def calculate_bcc(self, message):
        bcc = 0
        for byte in message:
            bcc ^= byte
        return bcc

    def open_connection(self, baudrate=300):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                time.sleep(0.2)

            self.ser = serial.Serial(
                port=self.port,
                baudrate=baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )

            if self.ser.is_open:
                time.sleep(0.2)
                return True
        except Exception as e:
            return False

    def send_request(self, request, calculate_bcc=False):
        try:

            if calculate_bcc:
                bcc = self.calculate_bcc(request)
                request += bytes([bcc])


            self.ser.write(request)
            self.ser.flush()
            time.sleep(0.3)
            return True
        except Exception as e:
            return False

    def read_response(self, timeout=2.0):
        try:
            start_time = time.time()
            response = bytearray()

            while (time.time() - start_time) < timeout:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response.extend(chunk)

                    if chunk.endswith(b'\x03') or chunk.endswith(b'!') or chunk.endswith(b'='):
                        break
                time.sleep(0.1)

            if response:
                return response
            else:
                return None

        except Exception as e:

            return None

    def read_meter(self):
        try:
            if not self.open_connection(300):
                return False

            if not self.send_request(b'/?!\r\n'):
                return False

            ident = self.read_response()
            if not ident:
                return False

 
            self.send_request(bytes([self.ACK]))
            time.sleep(0.2)

            if not self.send_request(b'050\r\n'):
                return False

            initial_response = self.read_response(timeout=1.0)
            if initial_response:
                self.ser.baudrate = 9600
                time.sleep(0.5)

                self.send_request(bytes([self.ACK]))
                time.sleep(0.3)

                read_request = bytes([self.SOH]) + b'R1' + bytes([self.STX]) + b'1.8.0()' + bytes([self.ETX])
                if not self.send_request(read_request, calculate_bcc=True):
                    return False

                data = self.read_response(timeout=3.0)
                if data:
                    try:
                        decoded_data = data.decode('ascii', errors='replace')
                        return decoded_data
                    except Exception as e:
                        return None
            else:
                return False

        except Exception as e:
            return False

        finally:
            if self.ser and self.ser.is_open:
                self.send_request(b'\x01B0\r\n')
                time.sleep(0.2)

                self.ser.close()


def read_meter_thread():
    while True:
        meter = IEC62056Reader()
        result = meter.read_meter()

        if result:
            data = {
                'timestamp': datetime.now().isoformat(),
                'data': result
            }
            if meter_data_queue.full():
                meter_data_queue.get()
            meter_data_queue.put(data)
            print(f"New meter data stored: {data}")

        time.sleep(60)


@app.route('/meter_data', methods=['GET'])
@limiter.limit("5 per minute")
def get_meter_data():
    try:
        if not meter_data_queue.empty():
            data = meter_data_queue.get()
            meter_data_queue.put(data)
            return jsonify(data)
        else:
            return jsonify({'error': 'No meter data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    meter_thread = threading.Thread(target=read_meter_thread, daemon=True)
    meter_thread.start()
