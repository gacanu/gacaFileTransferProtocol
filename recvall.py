import socket

# Read all bytes from the given socket until a newline char is reached.
def recvall(sock):
    BUFF_SIZE = 4096 # 4 KiB
    data = b''
    while not data.endswith(b'\n'):
       data += sock.recv(BUFF_SIZE)
    return data
