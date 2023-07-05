import socket
import json
import random
import pymysql


# import numpy as np
# import math


def generate_honeyword(pw):
    # 注意此处使用了绝对路径，文件迁移时需相应改变
    f = open('/home/osboxes/Desktop/gongkong_honeyword_server/cong.txt', 'r')
    result = f.readlines()
    l = []
    for i in result:
        l.append(i.strip('\n').split(','))

    # pw = input("\nEnter your password: ")

    M = (2.26 * len(pw)) // 3 + 1

    cnt = 0
    honeyword = []
    while cnt != M:
        l1 = random.sample(l, 8)
        l1 = set([tuple(t) for t in l1])
        # print(l1)
        seq0 = ''
        # seq1 = ''
        for i in list(set([tuple(t) for t in l1])):
            seq0 = seq0 + str(i[0]) + str(i[1]) + str(i[2])
        # seq1 = ''.join([i[1],seq1])
        # print(seq0)
        # print(seq1)

        num = 0
        seq1 = ''
        for i in pw:
            asc = ord(i)
            seq = seq0[num:num + len(str(asc))]
            num += len(str(asc))
            if asc < int(seq):
                asc += 1
            elif asc > int(seq):
                asc -= 1
            seq1 += chr(asc)
        honeyword.append(seq1)
        cnt += 1

    # print(honeyword)
    return honeyword


# socket客户端，服务端设置
SOCKET_CLIENT_IP = "127.0.0.1"
SOCKET_CLIENT_PORT = 5678
SOCKET_SERVER_IP = "127.0.0.1"
SOCKET_SERVER_PORT = 5679

# MySQL设置
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DATABASE = "gongkong_honeyword"


def honeyword_server():
    while True:
        # 通过socket接收信息
        ip_addr = (SOCKET_SERVER_IP, SOCKET_SERVER_PORT)
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(ip_addr)
        server.listen(5)

        conn, addr = server.accept()
        recv_msg = conn.recv(20480)
        server.close()

        recv_msg = json.loads(recv_msg.decode('utf-8'))

        # 注册阶段1，计算蜜语集合S
        if recv_msg['stage'] == 'register1':
            S = generate_honeyword(recv_msg['password'])
            send_msg = {'S': str(S)}
            print("本次计算的蜜语结果为"+str(S))

        # 注册阶段2，将ID和g插入数据库
        elif recv_msg['stage'] == 'register2':
            try:
                db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO user values ({id},{g});".format(id=recv_msg['id'], g=recv_msg['g'])
                )
                db.commit()
                cursor.close()
                db.close()
                send_msg = {'status': 'success'}
            except:
                send_msg = {'status': 'fail'}

        # 登录阶段，查询ID和g并将g和接收的y相比较
        elif recv_msg['stage'] == 'login':
            try:
                db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)
                cursor = db.cursor()
                cursor.execute(
                    "SELECT g FROM user WHERE id={id};".format(id=recv_msg['id'])
                )
                db.commit()
                g = cursor.fetchone()[0]
                cursor.close()
                db.close()
                if recv_msg['y'] != g:
                    send_msg = {'status': 'leakage'}
                else:
                    send_msg = {'status': 'success'}
            except:
                send_msg = {'status': 'fail'}

        # 修改密码阶段1，计算蜜语集合S
        elif recv_msg['stage'] == 'modify1':
            S = generate_honeyword(recv_msg['password'])
            send_msg = {'S': str(S)}
            print("本次计算的蜜语结果为" + str(S))

        # 修改密码阶段2，利用接收的ID和g更新数据库
        elif recv_msg['stage'] == 'modify2':
            try:
                db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)
                cursor = db.cursor()
                cursor.execute(
                    "UPDATE user SET g={g} WHERE id={id};".format(id=recv_msg['id'], g=recv_msg['g'])
                )
                db.commit()
                cursor.close()
                db.close()
                send_msg = {'status': 'success'}
            except:
                send_msg = {'status': 'fail'}

        # 通过socket发送信息
        ip_addr = (SOCKET_CLIENT_IP, SOCKET_CLIENT_PORT)
        client = socket.socket()
        # client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        client.connect(ip_addr)

        client.send(json.dumps(send_msg).encode('utf-8'))
        client.close()


if __name__ == '__main__':
    honeyword_server()
