import requests
import json
import os


class SensitiveWord:
    def __init__(self):


        # 计算配置文件绝对路径
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))

        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        #print(self.config)  # 输出配置文件内容以进行调试


        # 设置请求 URL
        self.url = "https://aip.baidubce.com/rest/2.0/antispam/v2/spam"

        # 获取 access token
        self.access_token = self.get_access_token()

    def get_access_token(self):
        """
        获取百度云接口的 access token

        :return: str access token
        
        """
        
        #检测敏感词配置是否存在
        if self.config is not None and self.config.get("common") is not None and self.config["common"].get("type") is not None:

            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.config["common"]["client_id"],
                "client_secret": self.config["common"]["client_secret"]
            }
            response = requests.post(url, params=params)
            response_json = response.json()

            access_token = response_json.get("access_token")

            if not access_token:
                raise ValueError(f"获取 access_token 失败: {response_json.get('error_description')}")
            
            #print(f"Access token: {access_token}")  # 输出访问令牌以进行调试
            return access_token
        else:
            print("百度云接口配置不存在")


    def process_text(self, text):

        #检测敏感词配置是否存在
        if self.config is not None and self.config.get("common") is not None and self.config["common"].get("type") is not None:
            #存在则执行正常检测流程
            url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"  # API 请求地址
            access_token = self.get_access_token()
            headers = {"content-type": "application/x-www-form-urlencoded"}
            params = {
                "text": text.encode("utf-8"),
                "access_token": access_token
            }
            response = requests.post(url, data=params, headers=headers)

            if response.status_code != 200:
                raise ValueError(f"无法连接到接口，请检查你的网络: {response.json().get('error_msg')}")

            conclusion_type = response.json().get("conclusionType")


            print(response.json())  # 输出完整的 API 响应结果

            if conclusion_type in [1, None]:
                return False
            else:
                return True
        #不存在则直接返回无敏感词
        else:
            return False
