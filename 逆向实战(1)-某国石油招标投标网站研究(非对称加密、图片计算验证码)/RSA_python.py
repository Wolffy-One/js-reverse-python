# _*_ coding: utf-8 _*_
import re
import time
import json

# execjs执行js文件出现有一些编码不能读取
import subprocess
from functools import partial
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs
from requests import Session


# 获取密钥
def get_css_pkey(RequestsSession):
    local_storage = {}
    timestamp = str(int(time.time() * 1000))
    headers = {
        "Machine_code": timestamp,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    response = RequestsSession.get('https://www.cnpcbidding.com/cms/css/bj.css', headers=headers)
    text = response.text
    text_list = re.findall(r"url\(data:image/png;base64,(.*?)\);", text)

    public_key = text_list[0]
    private_key = text_list[1]

    local_storage["logo1"] = public_key
    local_storage["logo2"] = private_key
    local_storage["time"] = timestamp

    return local_storage

# 通过验证码识别
def pass_captcha_check(RequestsSession):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    response = RequestsSession.get("https://www.cnpcbidding.com/cms/validateCode/undefined", headers=headers)
    message = response.json().get("message")
    # 这个验证码校验时间不确定，本着不占用资本主义资源的初心（不想浪费我薅到的羊毛）
    # 过了就不管他了
    if message == "验证码错误。":
        img_data = response.json().get("data")
        img_base64 = "data:image/png;base64," + img_data
        payload = {
            "image": img_base64,
            # 你们别想着薅羊毛，我已经重置了密钥
            "token": "ih2K5xPJLwZaRkURSyeNDqSabShiDZKBIBLR3xG4_z4",
            "type": "50100"
        }

        response = RequestsSession.post("http://api.jfbym.com/api/YmServer/customApi", headers={'Content-Type': 'application/json'}, data=json.dumps(payload))

        code = response.json().get("data").get("data")

        RequestsSession.get(f"https://www.cnpcbidding.com/cms/validateCode/{code}", headers=headers)

# 获取数据
def get_page_data(RequestsSession, local_storage):
    public_key = local_storage.get("logo1")
    private_key = local_storage.get("logo2")
    timestamp = local_storage.get("time")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "174",
        "Content-Type": "application/json;charset=UTF-8",
        "Host": "www.cnpcbidding.com",
        "Machine_code": timestamp,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }

    e = {
        "current": "1",  # 页码
        "size": "10",  # 每页数据
        "condition": {
            "columnId": "1",  # 分类导航栏
            "title": "",
            "projectType": ""
        }
    }

    # 读取js文件
    with open(r"RSA_js.js", "r", encoding='utf8') as f:
        js_str = f.read()
    """
        因为扣代码扣多了，js代码里面有一下字符在python读取的时候会有编码问题
        所以在导入execjs前需要加上一些东西（如下）：
        import subprocess
        from functools import partial
        subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
        import execjs
    """

    # 调用js文件里面的encruption加密方法
    data = execjs.compile(js_str).call('encruption', e, public_key)
    url = "https://www.cnpcbidding.com/cms/article/page"
    # 请求page接口
    response = RequestsSession.post(url, data=data, headers=headers)
    content = response.text
    # 通过decryption解密方法，获取实际数据
    decrypt_data = execjs.compile(js_str).call('decryption', content, private_key)
    return decrypt_data

# 入口
def main():
    RequestsSession = Session()

    local_storage = get_css_pkey(RequestsSession)

    pass_captcha_check(RequestsSession)

    data = get_page_data(RequestsSession, local_storage)

    print(data)

if __name__ == '__main__':
    main()
