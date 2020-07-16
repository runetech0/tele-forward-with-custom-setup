#!/usr/bin/python

from telethon import TelegramClient, events, errors
from telethon.events import StopPropagation
from configparser import ConfigParser
import json
import socks
import re
# import logging


config = ConfigParser()
config.read('conf.ini')


# logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
# level=logging.WARNING)

api_id = config['TELEGRAM']['api_id']
api_hash = config['TELEGRAM']['api_hash']
session_file = 'telegramBot'


sent_msgs = 0
# ##############################################< Proxy >##############################################

try:
    proxy_enabled = config['PROXY'].getboolean('enable')
    proxy_server = config['PROXY']['server'].encode()
    proxy_port = config['PROXY'].getint('port')
except KeyError:
    proxy_enabled = True
    proxy_server = '159.89.49.60'
    proxy_port = 31264
    pass


# if config['proxy']['enable']:
#     sockProxy = {
#         "proxy_type": socks.SOCKS5,
#         "addr": conf.SOCKS5_SERVER,
#         "port": conf.SOCKS5_PORT,
#         "rdns": True,
#         "username": conf.USERNAME,
#         "password": conf.PASSWORD
#     }


if proxy_enabled:
    # print(f'Using proxy server {proxy_server}:{proxy_port}')
    telegramClient = TelegramClient(session_file, api_id, api_hash, proxy=(
        socks.SOCKS5, proxy_server, proxy_port))
else:
    telegramClient = TelegramClient(session_file, api_id, api_hash)


def strToInt(strList):
    newList = []
    for i in strList:
        i = int(i)
        newList.append(i)
    return newList


un_filtered_source_channel = strToInt(list(config['UNFILTERED_CHANNELS'].keys()))
filtered_source_channel = strToInt(list(config['MEDIA_FILTERED_CHANNELS'].keys()))


def deEmojify(text):
    # A python function to remove emojis from string
    regrex_pattern = re.compile(pattern="["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)


def updateUI():
    global sent_msgs
    sent_msgs += 1
    print(f'[+] Forwarded Messages: {sent_msgs}', end='\r')


@telegramClient.on(events.NewMessage(chats=un_filtered_source_channel, blacklist_chats=False))
async def newMessageHandler(msg):
    print('Got message')
    src_chat = msg.chat_id
    dest_channels = strToInt(json.loads(config.get("UNFILTERED_CHANNELS", str(src_chat))))
    for channal in dest_channels:
        await telegramClient.send_message(channal, msg.message)
        updateUI()
    raise StopPropagation


@telegramClient.on(events.NewMessage(chats=filtered_source_channel, blacklist_chats=False))
async def filteredMessageHandler(msg):
    if msg.message.media:
        raise StopPropagation
    src_chat = msg.chat_id
    dest_channels = strToInt(json.loads(config.get("MEDIA_FILTERED_CHANNELS", str(src_chat))))
    for channal in dest_channels:
        emojiFiltered = deEmojify(msg.message.message)
        await telegramClient.send_message(channal, emojiFiltered)
        updateUI()
    raise StopPropagation


try:
    telegramClient.start()
    msg = '< Message Forward bot is up! >'
    print(f'\n{msg.center(len(msg)+30, "#")}\n')
    telegramClient.run_until_disconnected()
except KeyboardInterrupt:
    print("[+] Quiting bot!")
except errors.rpcerrorlist.ApiIdInvalidError:
    print("[+] Invalid API_ID/API_HASH")
