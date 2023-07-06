# encoding:utf-8

from model.model import Model
from config import model_conf, common_conf_val
from common import const
from common.log import logger
import requests
import time
import json
import os

sessions = {}

class YiyanModel(Model):
    def __init__(self):
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        self.api_key = model_conf(const.BAIDU).get('api_key')
        self.secret_key = model_conf(const.BAIDU).get('secret_key')
        self.access_token_response = self.obtain_access_key()
        self.ts = 1688529288
        now = time.time()
        if (now - self.ts) > int(self.access_token_response.get("expires_in",0)):
            self.access_token_response = self.obtain_access_key()
        self.access_token = self.access_token_response.get("access_token",None)

    def obtain_access_key(self):
        url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"%(self.api_key,self.secret_key)
        payload = ""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        resp = json.loads(response.text)
        return resp

    def query(self, messages=[]):
        payload = {
            "messages": messages
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.request(
            "POST", 
            "%s?access_token=%s"%(self.base_url,self.access_token), 
            headers = headers, 
            data = json.dumps(payload,ensure_ascii=False).encode('utf-8')
        )
        logger.info("[BAIDU] response.text={}".format(response.text))
        resp = json.loads(response.text)
        return resp

    def reply(self, query, context=None):
        logger.info("[BAIDU] context={}".format(json.dumps(context,ensure_ascii=False,indent=4)))
        logger.info("[BAIDU] query={}".format(query))
        from_user_id = context.get("from_user_id", "-1")
        messages = self.read_history_messages(from_user_id)
        message = {
            "role":"user",
            "content":query
        }
        messages.append(message)
        clear_memory_commands = common_conf_val('clear_memory_commands', ['#清除记忆'])
        reply_text = ""
        if query in clear_memory_commands:
            reply_text = "记忆已清除"
        else:
            resp = self.query(messages)
            need_clear_history=resp.get("need_clear_history",False)
            if need_clear_history:
                reply_text = "输入存在安全风险，已清理本次历史会话信息"
            else:
                reply_text=resp.get("result","")
        message = {
            "role":"assistant",
            "content":reply_text
        }
        messages.append(message)
        self.write_history_message(from_user_id, messages)
        return reply_text

    def read_history_messages(self, from_user_id):
        p = os.path.join(os.path.dirname(__file__),"../../")
        message_data_dir = os.path.join(p,"data","%s.txt"%(from_user_id))
        messages=[]
        if os.path.exists(message_data_dir):
            with open(message_data_dir,"r") as fr:
                messages = json.loads(fr.read())
        return messages

    def write_history_message(self, from_user_id, messages):
        p = os.path.join(os.path.dirname(__file__),"../../")
        message_data_dir = os.path.join(p,"data","%s.txt"%(from_user_id))
        with open(message_data_dir,"w") as fw:
            fw.write(json.dumps(messages, ensure_ascii=False, indent=4))
