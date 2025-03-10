import json
import requests
from urllib.parse import urljoin
import re

from utils.my_log import logger

def extract_and_parse_json(data_string):
    # logger.warning(data_string)
    # 如果 data_string 是 bytes 或 bytearray，将其解码为字符串
    if isinstance(data_string, (bytes, bytearray)):
        data_string = data_string.decode('utf-8')

    # logger.warning(data_string)
    # 使用正则表达式匹配 JSON 部分
    match = re.search(r'{.*}', data_string)
    if match:
        json_string = match.group(0).replace('\\', '')
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON string: {json_string}")
            return None
    
# from utils.common import Common
# from utils.logger import Configure_logger


class Langchain_ChatChat:
    def __init__(self, data):
        # self.common = Common()
        # 日志文件路径
        # file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        # Configure_logger(file_path)

        self.api_ip_port = data["api_ip_port"]
        self.chat_type = data["chat_type"]
        self.config_data = data

        self.history = []


    # 获取知识库列表
    def get_list_knowledge_base(self):
        url = urljoin(self.api_ip_port, "/knowledge_base/list_knowledge_bases")
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = extract_and_parse_json(result)

            if ret is None:
                logger.error("Failed to parse JSON: %s", result)
                # handle error here
            else:
                # continue with your code using parsed_json
                logger.debug(ret)
                logger.info(f"本地知识库列表：{ret['data']}")

            return ret['data']
        except Exception as e:
            logger.error(e)
            return None


    def get_resp(self, prompt):
        """请求对应接口，获取返回值

        Args:
            prompt (str): 你的提问

        Returns:
            str: 返回的文本回答
        """
        try:
            if self.chat_type == "模型":
                data_json = self.config_data["llm"]
                
                url = self.api_ip_port + "/chat/chat/completions"
            elif self.chat_type == "知识库":
                data_json = self.config_data["knowledge_base"]

                url = self.api_ip_port + "/chat/kb_chat"
            elif self.chat_type == "搜索引擎":
                data_json = self.config_data["search_engine"]

                url = self.api_ip_port + "/chat/kb_chat"
            else:
                data_json = self.config_data["llm"]
                url = self.api_ip_port + "/chat"

            if self.chat_type == "模型":
                import copy
                messages = copy.copy(self.history)
                messages.append({
                    "content": prompt,
                    "role": "user",
                    "name": "string"
                })
                data_json = {
                    "user": "string",
                    "messages": messages,
                    "model": self.config_data["llm"]["model"],
                    "max_tokens": 4096,
                    "response_format": {
                        "type": "text"
                    },
                    "stream": False,
                    "temperature": 0.7
                }
            elif self.chat_type == "知识库":
                data_json = {
                    "query": prompt,
                    "mode": "local_kb",
                    "kb_name": self.config_data["knowledge_base"]["kb_name"],
                    "top_k": self.config_data["knowledge_base"]["top_k"],
                    "score_threshold": self.config_data["knowledge_base"]["score_threshold"],
                    "history": self.history,
                    "stream": False,
                    "model": self.config_data["knowledge_base"]["model"],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "prompt_name": "default",
                    "return_direct": False
                }
            elif self.chat_type == "搜索引擎":
                data_json = {
                    "query": prompt,
                    "mode": "search_engine",
                    "kb_name": self.config_data["search_engine"]["search_engine_name"],
                    "top_k": self.config_data["search_engine"]["top_k"],
                    "score_threshold": self.config_data["knowledge_base"]["score_threshold"],
                    "history": self.history,
                    "stream": False,
                    "model": self.config_data["search_engine"]["model"],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "prompt_name": "default",
                    "return_direct": False
                }
            else:
                data_json["query"] = prompt
                data_json["history"] = self.history

            logger.warning(data_json)

            response = requests.post(url=url, json=data_json)
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = extract_and_parse_json(result)
            if ret is None:
                logger.error("Failed to parse JSON: %s", result)
                # handle error here
            else:
                # continue with your code using parsed_json
                logger.warning(ret)

                if self.chat_type == "模型":
                    resp_content = ret["choices"][0]["message"]["content"]
                elif self.chat_type == "知识库":
                    resp_content = ret["choices"][0]["message"]["content"]
                elif self.chat_type == "搜索引擎":
                    resp_content = ret["choices"][0]["message"]["content"]
                else:
                    resp_content = ret["choices"][0]["message"]["content"]

                # 启用历史就给我记住！
                if self.config_data["history_enable"]:
                    while True:
                        # 获取嵌套列表中所有字符串的字符数
                        total_chars = sum(len(string) for sublist in self.history for string in sublist)
                        # 如果大于限定最大历史数，就剔除第一个元素
                        if total_chars > self.config_data["history_max_len"]:
                            self.history.pop(0)
                        else:
                            self.history.append({"role": "user", "content": prompt, "name": "string"})
                            self.history.append({"role": "assistant", "content": resp_content, "name": "string"})
                            break

                return resp_content
        except Exception as e:
            logger.error(e)
            return None


if __name__ == '__main__':
    # 配置日志输出格式
    logger.basicConfig(
        level=logger.DEBUG,  # 设置日志级别，可以根据需求调整
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    data = {
        "api_ip_port": "http://127.0.0.1:7861",
        # 模型/知识库/搜索引擎
        "chat_type": "模型",
        "llm": {
            "stream": False,
            "model_name": "openai-api",
            "temperature": 0.7,
            "max_tokens": 4096,
            "prompt_name": "default"
        },
        "search_engine": {
            "search_engine_name": "metaphor",
            "top_k": 3,
            "stream": False,
            "model_name": "chatglm3-6b-int4",
            "temperature": 0.7,
            "max_tokens": 4096,
            "prompt_name": "default",
            "split_result": False
        },
        "knowledge_base" : {
            "knowledge_base_name": "astro",
            "top_k": 3,
            "score_threshold": 1,
            "stream": False,
            "model_name": "openai-api",
            "temperature": 0.7,
            "max_tokens": 4096,
            "prompt_name": "default"
        },
        "history_enable": True,
        "history_max_len": 300
    }
    langchain_chatchat = Langchain_ChatChat(data)


    if data["chat_type"] == "模型":
        logger.info(langchain_chatchat.get_resp("什么是黑洞"))
        logger.info(langchain_chatchat.get_resp("什么是原初黑洞"))
    elif data["chat_type"] == "知识库":  
        langchain_chatchat.get_list_knowledge_base()
        logger.info(langchain_chatchat.get_resp("什么是黑洞"))
        logger.info(langchain_chatchat.get_resp("什么是原初黑洞"))
    # please set BING_SUBSCRIPTION_KEY and BING_SEARCH_URL in os ENV
    elif data["chat_type"] == "搜索引擎":  
        logger.info(langchain_chatchat.get_resp("伊卡洛斯是谁"))
        logger.info(langchain_chatchat.get_resp("伊卡洛斯的英文名"))
    