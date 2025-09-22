# -*- coding: utf-8 -*-

import os
import argparse
import requests
import json 

from ..core.tuitui_api import TuiTuiBot
from ..core.ata360_api import Ata360Client

tuitui_client = TuiTuiBot(IM_APPID,IM_SECRET)
ata360_client = Ata360Client(ATA360_KEY)

recv_file_list = {}

def download_file(url,save_path,*args,**argv):
    if os.path.exists(save_path) == True:
        return True

    try:
        with requests.get(url, stream=True, *args,**argv) as response:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    
    except Exception as error:
        print(f"ERROR download_file {url} {error}")

        if os.path.exists(save_path):
            os.remove(save_path)

    return False

def ata360_submit_hash(hash_list):
    response = ata360_client.submit_task_by_hash(hash_list)

    code,msg = ata360_client.extrace_error_info(response)
    if code != 0:
        return msg
    return None
    
def ata360_submit_file(fileids):
    result = {}
    for fileid in fileids:
        file_path = f"{fileid}"

        if fileid not in recv_file_list:
            result[fileid] = "上传记录中文件ID未找到对于下载链接"
            continue

        if download_file(recv_file_list[fileid],file_path) == True and os.path.exists(file_path) == True:
            result[fileid] = ata360_client.extrace_error_info(ata360_client.submit_task_by_file([file_path]))
        else:
            result[fileid] = "下载指定文件失败"
    
    return result

def ata360_handler(args):
    if args.type == "submit_hash":
        return ata360_submit_hash(args.items)
    
    elif args.type == "submit_file":
        return ata360_submit_file(args.items)
    
    else:
        return "未知命令 f{args}"

def chat_parse_command(text):
    parser = argparse.ArgumentParser(prog="chatcli")
    subparsers  = parser.add_subparsers(dest='subcommand')

    ata_parser = subparsers.add_parser("ata")
    ata_parser.add_argument("type", choices=["submit_hash", "submit_file", "get_summary"], type=str)
    ata_parser.add_argument("items", nargs='+', type=str)
    ata_parser.set_defaults(func=ata360_handler)

    args = parser.parse_args(text.strip().split())
    return args.func(args)


def chat_handler(data:dict):
    msgtype = data["msgtype"]
    return_message = None

    try:
        
        if msgtype == "text":
            return_message = chat_parse_command(data["text"])
        
        elif msgtype == "file":
            recv_file_list[data["file"]["file_id"]]=data["file"]["url"]
            return_message = f"接收到文件 文件名:{data["file"]["name"]} 文件URL:{data["file"]["url"]} 文件ID:{data["file"]["file_id"]}"

    except Exception as error:
        print(f"ERROR chat_handler {data} {error}")
        
    return return_message

def single_chat_handler(data:dict):
    user_account = data["user_account"]

    response_text = chat_handler(data)
    if response_text != None:
        tuitui_client.send_text(response_text, [user_account])


def group_chat_handler(data:dict):
    user_account = data["user_account"]
    group_id = data["group_id"]

    response_text = chat_handler(data)
    if response_text != None:
        tuitui_client.send_text(response_text, None, [group_id], [user_account])

event_handler = {
    "single_chat" : single_chat_handler,
    "group_chat" : group_chat_handler
}
