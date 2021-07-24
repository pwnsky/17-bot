#!/usr/bin/python
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.friend import Friend
from graia.application.group import Group
from graia.application.entry import *
from graia.broadcast.entities.event import BaseEvent
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from graia.application.event import *
from graia.scheduler import timers
import graia.scheduler as scheduler
import asyncio
import requests
import threading
import urllib.request # 需要安装 urllib 库
from bs4 import BeautifulSoup #需要安装 bs4 库
import time
import os

# -----------------机器人配置---------------
loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:7777", 
        authKey="INITKEYIYt76fd4",         
        account=3202539766,           
        websocket=True 
    )
)
# -----------------机器人配置-----------------
 
# ------------------获得天气------------------
def get_weather():
    weather = ""
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64;\
    rv:23.0) Gecko/20100101 Firefox/23.0'}
    website = "http://www.tianqi.com/chengdu.html"
    req = urllib.request.Request(url=website, headers=header)
    page = urllib.request.urlopen(req)
    html = page.read()
    soup = BeautifulSoup(html.decode("utf-8"), "html.parser")
    nodes = soup.find_all('dd')
    info_list = []
    for node in nodes:
        temp = node.get_text()
        info_list.append(temp)
    weather = info_list[1] + info_list[2] + info_list[3].split('%',-1)[0] + "%"

    return weather 


# ------------------回复天气------------------
def reply_weather(msg):
    reply = None
    if "天气" in msg:
        reply = get_weather()
    return reply

      
# ------------------回复问候------------------
def reply_greetings(msg):
    reply = None
    if "安" in msg or "早" in msg or "午" in msg or "晚" in msg :
        if 6 < time.localtime().tm_hour and time.localtime().tm_hour < 11:
            reply = "早安"

        if 11 < time.localtime().tm_hour and time.localtime().tm_hour < 17:
            reply = "下午好"

        if 17 < time.localtime().tm_hour:
            reply = "晚安"

    return reply


# ------------------添加好友--------------------------
@bcc.receiver("NewFriendRequestEvent")
async def new_friend_request(event : NewFriendRequestEvent):
    print(event.nickname + ' 请求添加好友')
    await event.accept('我是十七')


# ------------------录入信息------------------
def reply_inpute(msg,friend):
    rmsg = None
    if "录入" in msg:
        msg = msg.replace("录入","")
        msg = msg.replace(" ","")
        uname, upasswd = msg.split(":")
        if uname.isascii and upasswd.isascii and len(uname) == 10:
            f =  open('./list', 'a')
            print(uname, upasswd)
            f.write(uname + ":" + upasswd + "\n")
            f.close()
            rmsg = "录入成功"
        else:
            rmsg = '''输入有误请检查格式
录入 帐号:密码 
如:
录入 123:456'''

    return rmsg


# ------------------监听消息--------------------------
@bcc.receiver("FriendMessage")
async def friend_message_listener(message: MessageChain, friend: Friend, app: GraiaMiraiApplication):
    print(str(friend.id) + " " + friend.nickname + " " + friend.remark)
    msg = message.asDisplay()
    rmsg = reply_main(msg,friend=friend)
    await app.sendFriendMessage(friend, MessageChain(__root__=[Plain( rmsg )]))


# ------------------回复模块--------------------------
def reply_main(msg, friend, group = None):

    reply = reply_inpute(msg, friend)
    if(reply != None):
        return reply

    reply = reply_greetings(msg)
    if(reply != None):
        return reply

    reply = reply_weather(msg)
    if(reply != None):
        return reply

    if reply == None:
        reply = '自动打卡机器人,输入"录入"录入信息后每天自动打卡'

    return reply


sche = scheduler.GraiaScheduler(loop=loop,broadcast=bcc)
@sche.schedule(timers.every_custom_seconds(1))
async def group_push_msg_scheduler():

    if(time.localtime().tm_hour == 7 and time.localtime().tm_min == 0):
        os.system('./clock.py')

    if(time.localtime().tm_hour == 7 and time.localtime().tm_min > 30 and time.localtime().tm_min < 33):
        rmsg =  '今天天气:' + get_weather() + '\n记得吃早饭喔!\n'
        friend_list = await app.friendList()
        for friend in friend_list:
            await app.sendFriendMessage(friend, MessageChain(__root__=[Plain( rmsg )]))
        time.sleep(180)

    if(time.localtime().tm_hour == 23 and time.localtime().tm_min > 30 and time.localtime().tm_min < 33):
        rmsg = "早点睡觉了喔,晚安!"
        friend_list = await app.friendList()
        for friend in friend_list:
            await app.sendFriendMessage(friend, MessageChain(__root__=[Plain( rmsg )]))
        time.sleep(180)

app.launch_blocking()
