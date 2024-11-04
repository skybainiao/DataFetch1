import requests
from requests.auth import HTTPBasicAuth
from queue import Queue
import threading
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

# 请求参数（根据需要修改）
params = {
    "sportId": 29,        # 示例：Soccer 的 sportId
    "leagueId": 1913,     # 示例联赛ID
    "eventId": 1600112155,  # 示例赛事ID
    "periodNumber": 0,    # 0 表示整场比赛
    "betType": "MONEYLINE",  # 示例：获取胜负的赔率
    "oddsFormat": "DECIMAL",  # 赔率格式为欧洲十进制
    "team": "TEAM1"  # 必填参数，指定投注的队伍
}

def fetch_odds():
    while True:
        start_time = time.time()
        # 从队列中获取一个账号
        username, password = account_queue.get()
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
            # 将账号放回队列末尾
            account_queue.put((username, password))
            # 计算请求结束的时间
            end_time = time.time()
            # 确保每次请求之间的间隔为1秒
            elapsed_time = end_time - start_time
            sleep_time = max(1 - elapsed_time, 0)
            time.sleep(sleep_time)

# 启动获取数据的主线程
fetch_odds()