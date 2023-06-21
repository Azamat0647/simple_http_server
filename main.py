import socket, select
from collections import deque

from settings import STATIC_PATH
import app


SERVER_ADDRESS = ('127.0.0.1', 8686)

# Говорит о том, сколько дескрипторов единовременно могут быть открыты
MAX_CONNECTIONS = 10

# Откуда и куда записывать информацию
INPUTS = list()
OUTPUTS = list()

WRITE_QUEUE = deque()


def get_non_blocking_server_socket():

    # Создаем сокет, который работает без блокирования основного потока
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)

    # Биндим сервер на нужный адрес и порт
    server.bind(SERVER_ADDRESS)

    # Установка максимального количество подключений
    server.listen(MAX_CONNECTIONS)

    return server


def handle_readables(readables, server):
    """
    Обработка появления событий на входах
    """
    for resource in readables:

        # Если событие исходит от серверного сокета, то мы получаем новое подключение
        if resource is server:
            connection, client_address = resource.accept()
            connection.setblocking(0)

            INPUTS.append(connection)
            print("new connection from {address}".format(address=client_address))

        # Если событие исходит не от серверного сокета, но сработало прерывание на наполнение входного буффера
        else:
            request = ""
            try:
                request = resource.recv(1024)

            # Если сокет был закрыт на другой стороне
            except ConnectionResetError:
                pass

            if request:
                request = request.decode('UTF-8')

                print('\nrequest: {} form {}'.format(request.split('\r\n')[0], 
                                                     resource.getpeername()))

                WRITE_QUEUE.append((resource, app.handling_request(request)))
                
                if resource not in OUTPUTS:
                    OUTPUTS.append(resource)

            # Если данных нет, но событие сработало, то ОС нам отправляет флаг о полном прочтении ресурса и его закрытии
            else:
                
                # Очищаем данные о ресурсе и закрываем дескриптор
                clear_resource(resource)


def clear_resource(resource):
    """
    Метод очистки ресурсов использования сокета
    """
    if resource in OUTPUTS:
        OUTPUTS.remove(resource)
    if resource in INPUTS:
        INPUTS.remove(resource)

    print('closing connection', resource)

    resource.close()


def handle_writables(writables):
    # Данное событие возникает когда в буффере на запись освобождается место
    last_res = WRITE_QUEUE[0][0]

    for resource in writables:
        if resource is last_res:
            try:
                responce = WRITE_QUEUE.popleft()[1]
                resource.send(responce)

                print('\nresponse sent to client:', resource.getpeername())
            except OSError:
                clear_resource(resource)
            


if __name__ == '__main__':

    # Создаем серверный сокет без блокирования основного потока в ожидании подключения
    server_socket = get_non_blocking_server_socket()
    INPUTS.append(server_socket)

    print("server is running on address " +  
          f"{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}, " + 
          "please, press ctrl+c to stop\n")
    try:
        while INPUTS:
            readables, writables, exceptional = select.select(INPUTS, OUTPUTS, INPUTS)
            if readables:
                handle_readables(readables, server_socket)
            if writables and WRITE_QUEUE:
                handle_writables(writables)
    except KeyboardInterrupt:
        for inp in INPUTS:
            clear_resource(inp)
        for out in OUTPUTS:
            clear_resource(out)

        print("\nServer stopped! Thank you for using!")