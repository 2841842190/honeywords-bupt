from django.shortcuts import render, redirect
import random
from . import honeyword_server_send, hash_pw, models


def register(request):
    # 通过session判断是否已经登录，如果已经登录，重定向至登录成功页面
    if request.session.get('id'):
        return redirect('/loginsuccess/')

    # 如果没有用户名或密码，返回页面；如果有，获取用户名和密码
    if not (request.POST.get("username") and request.POST.get("password")):
        return render(request, 'register.html')
    username = request.POST.get("username")
    password = request.POST.get("password")

    # 计算索引ID，此处ID使用数据库分配的ID
    if not models.User.objects.filter(username=username):
        models.User.objects.create(username=username, s='null')
    ID = models.User.objects.filter(username=username).values('identity')[0]['identity']

    # 发送到蜜语服务器，接收蜜语集合S
    recv_msg = honeyword_server_send.honeyword_server_send({
        'stage': 'register1',
        'password': password
    })
    S = eval(recv_msg['S'])
    print(S)

    # 为了和哈希后的密码等长，对S进行哈希
    S = [hash_pw.hash_pw(word) for word in S]

    # 将密码进行哈希，并将密码插入S以及打乱顺序重新排列
    password = hash_pw.hash_pw(password)
    S.append(password)
    random.shuffle(S)

    # 将S存入数据库
    models.User.objects.filter(identity=ID).update(s=str(S))

    # 获取ID以及密码在S中的位置索引并发送到蜜语服务器
    recv_msg = honeyword_server_send.honeyword_server_send({
        'stage': 'register2',
        'id': ID,
        'g': S.index(password)
    })

    # 如果蜜语服务器操作数据库失败，为保持数据一致，删除数据库此处新增的记录，并提示注册失败
    if recv_msg['status'] == 'fail':
        models.User.objects.filter(identity=ID).delete()
        return render(request, 'register.html', {'status': '注册失败'})
    return redirect('/login/')


def login(request):
    # 通过session判断是否已经登录，如果已经登录，重定向至登录成功页面
    if request.session.get('id'):
        return redirect('/loginsuccess/')

    # 如果没有用户名或密码，返回页面；如果有，获取用户名和密码
    if not (request.POST.get("username") and request.POST.get("password")):
        return render(request, 'login.html')
    username = request.POST.get("username")
    password = request.POST.get("password")

    # 查看ID是否在数据库中，如果不存在，提示用户未注册；如果存在，将用户名映射为ID
    if not models.User.objects.filter(username=username):
        return render(request, 'login.html', {'status': "用户未注册"})
    ID = models.User.objects.filter(username=username).values('identity')[0]['identity']

    # 将密码进行哈希，获取S，查看密码是否在S中
    password = hash_pw.hash_pw(password)
    S = models.User.objects.filter(identity=ID).values('s')[0]['s']
    S = eval(S)

    # 如果密码不在S中，log数据库增加一条非蜜语登录错误的记录，并提示用户密码错误
    if password not in S:
        # 获取IP
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            IP = request.META.get('HTTP_X_FORWARDED_FOR')
        else:
            IP = request.META.get('REMOTE_ADDR')
        print(type(IP), IP)

        models.Loginlog.objects.create(identity=ID, ip=IP, is_honeyword=False)
        return render(request, 'login.html', {'status': "用户密码错误"})

    # 如果密码在S中，发送到蜜语服务器进行比较
    recv_msg = honeyword_server_send.honeyword_server_send({
        'stage': 'login',
        'id': ID,
        'y': S.index(password)
    })

    # 如果蜜语服务器返回‘leakage’，表示蜜语可能泄露，log数据库增加一条蜜语登录错误的记录，但依旧提示用户密码错误
    if recv_msg['status'] == 'leakage':
        # 获取IP
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            IP = request.META.get('HTTP_X_FORWARDED_FOR')
        else:
            IP = request.META.get('REMOTE_ADDR')
        print(type(IP), IP)

        models.Loginlog.objects.create(identity=ID, ip=IP, is_honeyword=True)
        return render(request, 'login.html', {'status': "用户密码错误"})

    # 如果蜜语服务器操作数据库失败，提示用户服务器故障
    elif recv_msg['status'] == 'fail':
        return render(request, 'login.html', {'status': "服务器故障"})

    # 登录成功，设置session
    request.session['id'] = ID
    request.session.set_expiry(300)
    return redirect('/loginsuccess/')


def login_success(request):
    # 通过session判断是否已经登录，如果尚未登录，重定向至登录页面
    if not request.session.get('id'):
        return redirect('/login/')

    # 通过session的ID获取用户名以及log数据库的记录，返回页面
    ID = request.session.get('id')
    username = models.User.objects.filter(identity=ID).values('username')[0]['username']
    login_log_id = models.Loginlog.objects.filter(identity=ID)
    login_log_id_honeyword = login_log_id.filter(is_honeyword=True)
    print(login_log_id, type(login_log_id))

    if len(login_log_id_honeyword) >= 3:
        return render(request, 'leakage.html',
                      {'username': username, 'wrong_pw': len(login_log_id), 'hw_pw': len(login_log_id_honeyword)})
    else:
        return render(request, 'welcome.html', {'username': username})


def login_exit(request):
    # 删除session信息，重定向至登录页面
    request.session.flush()
    return redirect('/login/')


def modify_password(request):
    # 通过session判断是否已经登录，如果尚未登录，重定向至登录页面
    if not request.session.get('id'):
        return redirect('/login/')

    # 如果没有密码，返回页面；如果有，获取密码
    if not request.POST.get("password"):
        return render(request, 'change_password.html')
    password = request.POST.get("password")

    # 通过session获取ID
    ID = request.session.get('id')

    # 修改密码时删除log数据库中的记录
    models.Loginlog.objects.filter(identity=ID).delete()

    # 保存原来的S
    save_S = models.User.objects.filter(identity=ID).values('s')[0]['s']

    # 发送到蜜语服务器，接收蜜语集合S
    recv_msg = honeyword_server_send.honeyword_server_send({
        'stage': 'modify1',
        'password': password
    })
    S = eval(recv_msg['S'])
    print(S)

    # 为了和哈希后的密码等长，对S进行哈希
    S = [hash_pw.hash_pw(word) for word in S]

    # 将密码进行哈希，并将密码插入S以及打乱顺序重新排列
    password = hash_pw.hash_pw(password)
    S.append(password)
    random.shuffle(S)

    # 将S存入数据库
    models.User.objects.filter(identity=ID).update(s=str(S))

    # 获取ID以及密码在S中的位置索引并发送到蜜语服务器
    recv_msg = honeyword_server_send.honeyword_server_send({
        'stage': 'modify2',
        'id': ID,
        'g': S.index(password)
    })

    # 如果蜜语服务器操作数据库失败，为保持数据一致，恢复数据库此处的记录，并提示修改密码失败
    if recv_msg['status'] == 'fail':
        models.User.objects.filter(identity=ID).update(s=save_S)
        return render(request, 'change_password.html', {'status': '修改密码失败'})
    return redirect('/loginsuccess/')
