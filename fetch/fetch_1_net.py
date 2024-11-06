from datetime import datetime, timedelta, time
import time
from datetime import datetime
import pytz
import requests
from requests.auth import HTTPBasicAuth

# 使用固定的API账号和密码
username = "E01AA0NDM1"
password = "dddd1111"


# 获取所有运动类型
def get_all_sports():
    """获取所有运动类型"""
    url_sports = "https://api.ps3838.com/v3/sports"
    try:
        response = requests.get(url_sports, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            sports_data = response.json()
            print("运动类型列表:", sports_data)
            return sports_data.get("sports", [])
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"账号 {username} 请求发生错误: {e}")
        return None


# 通过运动类型ID获取所有联赛
def get_leagues_by_sport(sport_id):
    """通过运动类型ID获取所有联赛"""
    url_leagues = "https://api.ps3838.com/v3/leagues"
    params = {"sportId": sport_id}
    try:
        response = requests.get(url_leagues, params=params, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            leagues_data = response.json()
            print(f"运动类型ID {sport_id} 的联赛信息:", leagues_data.get("leagues", []))
            return leagues_data.get("leagues", [])
        else:
            print(f"请求失败，运动类型ID {sport_id}，状态码: {response.status_code}, 错误信息: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"账号 {username} 请求发生错误: {e}")
        return None


def find_denmark_superliga():
    """查找足球中 Denmark - Superliga 联赛"""
    sport_id = 29  # 足球的运动类型ID
    leagues = get_leagues_by_sport(sport_id)  # 获取足球下的所有联赛
    if leagues:
        for league in leagues:
            league_name = league.get('name')
            if league_name == "Denmark - Superliga":
                print(f"找到联赛: {league_name}, 联赛ID: {league['id']}")
                return league
        print("未找到 Denmark - Superliga 联赛")
        return None
    else:
        print("获取联赛信息失败")
        return None


def get_live_or_upcoming_open_fixtures(sport_id, league_id):
    """获取某个联赛下的所有正在进行或即将开始且状态为 'O' 的比赛"""
    url_fixtures = "https://api.ps3838.com/v3/fixtures"
    params = {"sportId": sport_id, "leagueIds": league_id}
    try:
        response = requests.get(url_fixtures, params=params, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            fixtures_data = response.json()
            # 筛选条件：status为'O'，表示开放投注的比赛
            open_fixtures = [
                fixture for league in fixtures_data['league'] for fixture in league['events']
                if fixture.get('status') == 'O'
            ]
            return open_fixtures
        else:
            print(f"请求失败，联赛ID {league_id}，状态码: {response.status_code}, 错误信息: {response.text}")
            return None
    except requests.exceptions.RequestException as e:

        return None


# 新增方法：获取所有足球联赛的未结算比赛
def get_all_unsettled_fixtures(sport_id):
    """获取所有足球联赛的未结算比赛"""
    all_unsettled_fixtures = []

    leagues = get_leagues_by_sport(sport_id)  # 获取所有足球联赛
    if leagues:
        for league in leagues:
            league_id = league['id']
            # 获取当前联赛的开放投注比赛
            unsettled_fixtures = get_live_or_upcoming_open_fixtures(sport_id, league_id)
            if unsettled_fixtures:
                all_unsettled_fixtures.extend(unsettled_fixtures)

    print(f"所有未结算比赛总数: {len(all_unsettled_fixtures)}")
    return all_unsettled_fixtures


def get_today_open_fixtures(sport_id):
    """获取某个运动类型下的所有今日开放投注的比赛"""
    all_today_open_fixtures = []

    # 获取所有运动类型下的联赛
    leagues = get_leagues_by_sport(sport_id)
    if leagues:
        today = datetime.now(pytz.timezone('Asia/Shanghai')).date()  # 获取今天的日期

        for league in leagues:
            league_id = league['id']
            # 获取当前联赛的所有比赛
            fixtures = get_live_or_upcoming_open_fixtures(sport_id, league_id)
            if fixtures:
                # 筛选条件：status为'O'，并且比赛开始时间为今天
                today_fixtures = [
                    fixture for fixture in fixtures
                    if datetime.strptime(fixture['starts'], '%Y-%m-%dT%H:%M:%SZ').date() == today
                ]
                if today_fixtures:
                    all_today_open_fixtures.extend(today_fixtures)
                    print(f"联赛ID {league_id} 今日开放投注比赛信息:", today_fixtures)

    print(f"所有今日开放投注比赛总数: {len(all_today_open_fixtures)}")
    return all_today_open_fixtures


def get_in_running_football_events():
    """获取足球进行中的赛事"""
    url = "https://api.ps3838.com/v2/inrunning"
    params = {
        "sportId": 29  # 足球的运动类型ID
    }

    try:
        response = requests.get(url, params=params, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            running_data = response.json()
            if 'sports' in running_data and running_data['sports']:
                football_data = running_data['sports'][0]  # 足球的所有联赛和赛事数据
                print("进行中的足球赛事数据:", football_data)
                return football_data
            else:
                print("没有进行中的足球赛事。")
                return None
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None


# 基础URL
base_url = "https://api.ps3838.com"


def get_all_odds_and_lines(event_id, sport_id, odds_format="Decimal"):
    """
    获取指定比赛的所有赔率和盘口信息，增加数据验证避免无效请求。
    返回赔率和盘口数据分别为单独行。
    """
    odds_endpoint = f"{base_url}/v3/odds"
    odds_params = {
        "sportId": sport_id,
        "eventIds": event_id,
        "oddsFormat": odds_format
    }

    try:
        odds_response = requests.get(odds_endpoint, params=odds_params, auth=HTTPBasicAuth(username, password))

        if odds_response.status_code != 200:
            print(f"获取赔率失败: {odds_response.status_code} - {odds_response.text}")
            return None

        odds_data = odds_response.json()

        if not odds_data.get('leagues') or not odds_data['leagues'][0].get('events'):
            print(f"比赛 {event_id} 没有赔率信息。")
            return {"error": "no_odds_available"}

        league_id = odds_data['leagues'][0]['id']
        periods = odds_data['leagues'][0]['events'][0]['periods']

        line_data = []

        for period in periods:
            period_number = period['number']
            line_id = period['lineId']

            for bet_type in ["SPREAD", "TOTAL_POINTS", "MONEYLINE"]:
                line_params = {
                    "sportId": sport_id,
                    "leagueId": league_id,
                    "eventId": event_id,
                    "periodNumber": period_number,
                    "betType": bet_type,
                    "oddsFormat": odds_format,
                }

                # 针对 SPREAD 盘口
                if bet_type == "SPREAD" and "spreads" in period and period['spreads']:
                    line_params["handicap"] = period['spreads'][0].get('hdp')
                    line_params["team"] = "TEAM1"  # 默认值
                    if not line_params["handicap"]:
                        continue

                # 针对 TOTAL_POINTS 盘口
                elif bet_type == "TOTAL_POINTS" and "totals" in period and period['totals']:
                    line_params["handicap"] = period['totals'][0].get('points')
                    line_params["side"] = "OVER"  # 默认值
                    if not line_params["handicap"]:
                        continue

                # 针对 MONEYLINE 盘口
                elif bet_type == "MONEYLINE":
                    line_params["team"] = "TEAM1"  # 默认值

                # 请求具体盘口数据
                line_endpoint = f"{base_url}/v2/line"
                line_response = requests.get(line_endpoint, params=line_params, auth=HTTPBasicAuth(username, password))

                if line_response.status_code == 200:
                    line_info = line_response.json()
                    if line_info.get("status") == "SUCCESS":
                        line_data.append({
                            "betType": bet_type,
                            "lineInfo": line_info
                        })
                else:
                    continue

        print("Odds:", odds_data)  # 打印赔率
        print("Lines:", line_data)  # 打印盘口数据

    except requests.exceptions.RequestException as e:
        pass



def get_today_soccer_inrunning():
    """
    获取所有足球联赛的今日滚球比赛，并显示联赛ID和比赛ID。
    """
    url = "https://api.ps3838.com/v2/inrunning"

    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            data = response.json()

            if 'sports' in data and data['sports']:
                football_data = data['sports'][0]  # 获取足球数据
                leagues = football_data.get('leagues', [])

                for league in leagues:
                    league_id = league.get('id', 'Unknown League ID')
                    print(f"League ID: {league_id}")

                    events = league.get('events', [])
                    for event in events:
                        event_id = event.get('id', 'Unknown Match ID')
                        print(f"  Event ID: {event_id}")
            else:
                print("没有进行中的足球赛事。")
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")


def get_league_names():
    """获取所有足球联赛的名称"""
    url = f"{base_url}/v3/leagues"
    params = {"sportId": 29}  # 足球
    response = requests.get(url, params=params, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        leagues_data = response.json().get("leagues", [])
        return {league['id']: league['name'] for league in leagues_data}
    else:
        print(f"获取联赛名称失败: {response.status_code} - {response.text}")
        return {}


def get_fixture_names(league_ids):
    """获取指定联赛的比赛详细信息，包括主队、客队和比赛时间"""
    url = f"{base_url}/v3/fixtures"

    # 获取北京时间当天的起始时间和结束时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    today_start = int(
        time.mktime(datetime.now(beijing_tz).replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
    today_end = int(
        time.mktime(datetime.now(beijing_tz).replace(hour=23, minute=59, second=59, microsecond=0).timetuple()))

    params = {
        "sportId": 29,  # 足球
        "leagueIds": ','.join(map(str, league_ids)),
        "since": today_start,  # 北京时间的起点时间
        "until": today_end  # 北京时间的终点时间
    }

    response = requests.get(url, params=params, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        fixtures_data = response.json().get("leagues", [])
        if not fixtures_data:
            print("No fixtures available for the given league IDs and time range.")
            return {}

        fixture_dict = {}
        for league in fixtures_data:
            for event in league['events']:
                fixture_dict[event['id']] = {
                    "home": event.get('home', 'Unknown Home Team'),
                    "away": event.get('away', 'Unknown Away Team'),
                    "start_time": event.get('startTime', 'Unknown Start Time')
                }
        return fixture_dict
    else:
        print(f"获取比赛名称失败: {response.status_code} - {response.text}")
        return {}


def display_running_matches():
    """
    获取所有足球联赛的今日滚球比赛，并显示联赛名称和比赛队伍。
    """
    url = f"{base_url}/v2/inrunning"

    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            data = response.json()

            if 'sports' in data and data['sports']:
                football_data = data['sports'][0]
                leagues = football_data.get('leagues', [])

                league_names = get_league_names()  # 获取联赛名称
                for league in leagues:
                    league_id = league.get('id', 'Unknown League ID')
                    league_name = league_names.get(league_id, 'Unknown League')
                    print(f"League: {league_name}")

                    events = league.get('events', [])
                    for event in events:
                        event_id = event.get('id', 'Unknown Event ID')
                        home_team = event.get('home', 'Unknown Home Team')
                        away_team = event.get('away', 'Unknown Away Team')
                        print(f"  Match: {home_team} vs {away_team} (Event ID: {event_id})")
            else:
                print("没有进行中的足球赛事。")
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")


def get_event_details(event_ids):
    """
    根据Event ID获取比赛详细信息。
    支持单个或多个Event ID。
    """
    url = "https://api.ps3838.com/v3/fixtures"

    # 确保event_ids是一个列表，即使是单个ID
    if isinstance(event_ids, int):
        event_ids = [event_ids]

    params = {
        "sportId": 29,  # 足球的运动类型ID
        "eventIds": ','.join(map(str, event_ids))  # 将Event ID转换为逗号分隔的字符串
    }

    try:
        response = requests.get(url, params=params, auth=HTTPBasicAuth(username, password))
        if response.text != '':
            print(f"获取到的比赛信息: {response.text}")
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None

# 调用方法


# 调用方法
get_in_running_football_events()
display_running_matches()



events_to_check = [1600298676,1600298675,1600352129,1600352131]
for event in events_to_check:
    get_event_details(event)

    get_all_odds_and_lines(event, 29)

