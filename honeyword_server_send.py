import socket
import json


def honeyword_server_send(msg):
    ip_addr = ("127.0.0.1", 5679)
    client = socket.socket()
    # client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    client.connect(ip_addr)

    client.send(json.dumps(msg).encode('utf-8'))
    client.close()

    ip_addr = ("127.0.0.1", 5678)
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ip_addr)
    server.listen(5)

    conn, addr = server.accept()
    recv_msg = conn.recv(20480)
    recv_msg = json.loads(recv_msg.decode('utf-8'))
    server.close()

    return recv_msg


if __name__ == '__main__':
    print(type(honeyword_server_send({'stage': 'register', 'password': 'butian'})))
    print(honeyword_server_send({'stage': 'register', 'password': 'bu'}))
    print(type(honeyword_server_send({'stage': 'register', 'password': 'butianzheng'})))
