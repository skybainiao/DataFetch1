import requests
from requests.auth import HTTPBasicAuth

# 用户的API账号和密码
username = "E01AA0NDM1"
password = "dddd1111"


def get_all_sports():
    """获取所有运动类型"""
    url_sports = "https://api.ps3838.com/v3/sports"
    response = requests.get(url_sports, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        sports_data = response.json()
        print("运动类型列表:", sports_data)
        return sports_data
    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
        return None


def get_football_leagues():
    """获取足球的所有联赛"""
    url_leagues = "https://api.ps3838.com/v3/leagues"
    params = {
        "sportId": 29  # Soccer 的 sportId
    }
    response = requests.get(url_leagues, params=params, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        try:
            leagues_data = response.json()
            for league in leagues_data.get('leagues', []):
                print(f"联赛名称: {league['name']}, 联赛ID: {league['id']}")
            return leagues_data
        except ValueError:
            print("无法解析响应为JSON，原始响应内容:", response.text)
            return None
    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
        return None


def get_live_league_fixtures(league_id):
    """获取某个足球联赛的所有滚球（live）类型的比赛"""
    url_fixtures = "https://api.ps3838.com/v3/fixtures"
    params = {
        "sportId": 29,    # Soccer 的 sportId
        "leagueIds": league_id,  # 联赛的 leagueId
        "live": True  # 只获取滚球类型的比赛
    }
    response = requests.get(url_fixtures, params=params, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        try:
            fixtures_data = response.json()
            print("联赛中的滚球赛事列表:", fixtures_data)
            return fixtures_data
        except ValueError:
            print("无法解析响应为JSON，原始响应内容:", response.text)
            return None
    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
        return None


def get_live_event_details(league_id, event_id):
    """获取某场滚球比赛的详细数据"""
    url_event_details = "https://api.ps3838.com/v2/line"
    params = {
        "sportId": 29,        # Soccer 的 sportId
        "leagueId": league_id,  # 联赛的 leagueId
        "eventId": event_id,    # 某个赛事的 eventId
        "periodNumber": 0,    # 0 表示整场比赛
        "betType": "MONEYLINE",  # 示例：获取胜负的赔率
        "oddsFormat": "DECIMAL",  # 赔率格式为欧洲十进制
        "team": "TEAM1"  # 必填参数，指定投注的队伍
    }
    response = requests.get(url_event_details, params=params, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        try:
            event_data = response.json()
            print("滚球比赛的详细数据:", event_data)
            return event_data
        except ValueError:
            print("无法解析响应为JSON，原始响应内容:", response.text)
            return None
    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
        return None

def get_leagues_by_country(country_name):
    """获取某个国家的所有联赛"""
    leagues_data = get_football_leagues()
    if leagues_data:
        country_leagues = [
            league for league in leagues_data.get('leagues', [])
            if country_name.lower() in league['name'].lower()
        ]
        for league in country_leagues:
            print(f"联赛名称: {league['name']}, 联赛ID: {league['id']}")
        return country_leagues
    else:
        print(f"未找到与国家 {country_name} 相关的联赛")
        return None

'''
# 示例调用
get_all_sports()
leagues = get_football_leagues()
if leagues:
    league_id = 1913  # 示例联赛ID
    live_fixtures = get_live_league_fixtures(league_id)
    if live_fixtures:
        event_id = 1600112155  # 示例赛事ID
        get_live_event_details(league_id, event_id)
'''
'''
# 获取某个国家的所有联赛
get_leagues_by_country("Denmark")
'''

