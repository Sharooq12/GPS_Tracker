import socket
import time

serverAddress = ('192.168.242.126', 2222)
bufferSize = 1024
UDPClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    UDPClient.sendto(b'', serverAddress)  # Sending an empty message or a placeholder
    data, address = UDPClient.recvfrom(bufferSize)

    if data:
        print('Data from Server:', data.decode('utf-8'))
    else:
        print('No data received. Waiting for the next message...')
    time.sleep(1)

