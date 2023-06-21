import socket

MAX_CONNECTIONS = 20
address_to_server = ('127.0.0.1', 9090)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(address_to_server)


client.send(bytes("hello from client number 1", encoding='UTF-8'))

data = client.recv(1024)
print(str(data))

client.close()