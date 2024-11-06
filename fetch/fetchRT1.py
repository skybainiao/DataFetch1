import requests
from requests.auth import HTTPBasicAuth
from queue import Queue
import time

# 用户的API账号和密码列表
accounts = [
    ("GA1A711D00", "dddd1111"),
    ("GA1A711D01", "dddd1111"),
    ("GA1A711D02", "dddd1111"),
    ("GA1A711D03", "dddd1111"),
    ("GA1A711D04", "dddd1111"),
    ("GA1A711D05", "dddd1111"),
    ("GA1A711D06", "dddd1111"),
    ("GA1A711D07", "dddd1111"),
    ("GA1A711D08", "dddd1111"),
    ("GA1A711D09", "dddd1111")
]

# 创建一个账号队列
account_queue = Queue()
for account in accounts:
    account_queue.put(account)

# 请求URL
url_odds = "https://api.ps3838.com/v2/line"

def fetch_odds(event_id, sport_id=4):
    """获取实时赔率数据"""
    while True:
        start_time = time.time()
        username, password = account_queue.get()
        params = {
            "sportId": sport_id,
            "eventId": event_id,
            "periodNumber": 0,
            "betType": "MONEYLINE",
            "oddsFormat": "DECIMAL"
        }

        try:
            response = requests.get(url_odds, params=params, auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                odds_data = response.json()
                print(f"账号 {username} 获取到的赔率数据:", odds_data)
            else:
                print(f"账号 {username} 请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"账号 {username} 请求发生错误: {e}")
        finally:
            account_queue.put((username, password))
            # 确保每次请求之间的间隔为1秒
            elapsed_time = time.time() - start_time
            time.sleep(max(1 - elapsed_time, 0))

# 由于fetch_odds的调用是在fetch_1_net.py中完成，因此此文件不需要示例调用部分
