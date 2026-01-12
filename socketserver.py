import socket
import serial
import time

def parse_gprmc(data):
    parts = data.strip().split(b',')
    if len(parts) >= 12 and parts[0] == b'$GPRMC':
        # Extract latitude and longitude
        lat_raw = parts[3]
        lng_raw = parts[5]

        if lat_raw and lng_raw:
            lat_deg = float(lat_raw[:2])
            lat_min = float(lat_raw[2:]) / 60.0
            lat = lat_deg + lat_min

            lng_deg = float(lng_raw[:3])
            lng_min = float(lng_raw[3:]) / 60.0
            lng = lng_deg + lng_min

            return lat, lng

    return None, None

def gps_reader():
    ServerPort = 2222
    ServerIP = '192.168.108.126'
    bufferSize = 1024
    bytesToSend = b''  # Placeholder for now

    RPIsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    RPIsocket.bind((ServerIP, ServerPort))
    print('Server is Up and Listening . . .')

    while True:
        port = "/dev/ttyAMA0"
        ser = serial.Serial(port, baudrate=9600, timeout=0.5)
        newdata = ser.readline()

        lat, lng = parse_gprmc(newdata)

        if lat is not None and lng is not None:
            # Print latitude and longitude in the server
            print('Latitude:', lat, 'Longitude:', lng)

            # Create a message with latitude and longitude
            message = 'Latitude: {}, Longitude: {}'.format(lat, lng)
            bytesToSend = message.encode('utf-8')

        # Send the message to the client
        client_message, address = RPIsocket.recvfrom(bufferSize)
        RPIsocket.sendto(bytesToSend, address)

if __name__ == '__main__':
    gps_reader()
