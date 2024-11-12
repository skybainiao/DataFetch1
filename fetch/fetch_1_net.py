from datetime import time, datetime
import pytz
import requests
from requests.auth import HTTPBasicAuth
import threading
import time
import csv

# 使用固定的API账号和密码
username = "E01AA0NDM1"
password = "dddd1111"
# 基础URL
base_url = "https://api.ps3838.com"


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


def v2running():
    """获取足球进行中的赛事"""
    url = "https://api.ps3838.com/v2/inrunning"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            running_data = response.json()
            print("进行中的足球赛事数据:", running_data)
            return running_data
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return None


def getFootball_today_info():
    """
    获取所有足球联赛的今日滚球比赛，并分类显示每个联赛下的比赛详细信息，包括主客队名称。
    """
    url_inrunning = f"{base_url}/v2/inrunning"
    url_fixtures = f"{base_url}/v3/fixtures"

    try:
        # 第一步：获取今日进行中的比赛信息
        response_inrunning = requests.get(url_inrunning, auth=HTTPBasicAuth(username, password))

        if response_inrunning.status_code == 200:
            inrunning_data = response_inrunning.json()

            if 'sports' in inrunning_data and inrunning_data['sports']:
                football_data = inrunning_data['sports'][0]
                leagues = football_data.get('leagues', [])

                all_event_ids = []
                league_id_name_map = {}

                for league in leagues:
                    league_id = league.get('id', 'Unknown League ID')
                    league_name = league.get('name', 'Unknown League')
                    league_id_name_map[league_id] = league_name
                    events = league.get('events', [])
                    event_ids = [event.get('id') for event in events if event.get('id')]

                    all_event_ids.extend(event_ids)

                if not all_event_ids:
                    print("没有进行中的足球赛事。")
                    return

                # 第二步：一次性获取所有比赛的详细信息
                params = {
                    "sportId": 29,  # 足球
                    "eventIds": ','.join(map(str, all_event_ids))
                }
                response_fixtures = requests.get(url_fixtures, params=params,
                                                 auth=HTTPBasicAuth(username, password))

                if response_fixtures.status_code == 200:
                    fixtures_data = response_fixtures.json()

                    if 'league' in fixtures_data:
                        leagues_data = fixtures_data['league']
                        for league_data in leagues_data:
                            league_id = league_data.get('id', 'Unknown League ID')
                            league_name = league_data.get('name', 'Unknown League')

                            print(f"\nLeague: {league_name} (League ID: {league_id})")

                            for event in league_data.get('events', []):
                                home_team = event.get('home', 'Unknown Home Team')
                                away_team = event.get('away', 'Unknown Away Team')
                                start_time = event.get('starts', 'Unknown Start Time')
                                event_id = event.get('id', 'Unknown ID')
                                print(
                                    f"  Match: {home_team} vs {away_team} | Start: {start_time} (Event ID: {event_id})")
                    else:
                        print("没有比赛的详细信息。")
                else:
                    print(f"获取比赛详情失败，状态码: {response_fixtures.status_code}")
            else:
                print("没有进行中的足球赛事。")
        else:
            print(f"请求滚球比赛数据失败，状态码: {response_inrunning.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")


def getFootball_today_infoForServer():
    """
    获取所有足球联赛的今日滚球比赛，并分类返回每个联赛下的比赛详细信息，包括主客队名称。
    """
    url_inrunning = f"{base_url}/v2/inrunning"
    url_fixtures = f"{base_url}/v3/fixtures"

    try:
        # 第一步：获取今日进行中的比赛信息
        response_inrunning = requests.get(url_inrunning, auth=HTTPBasicAuth(username, password))

        if response_inrunning.status_code == 200:
            inrunning_data = response_inrunning.json()

            if 'sports' in inrunning_data and inrunning_data['sports']:
                football_data = inrunning_data['sports'][0]
                leagues = football_data.get('leagues', [])

                all_event_ids = []
                league_id_name_map = {}

                for league in leagues:
                    league_id = league.get('id', 'Unknown League ID')
                    league_name = league.get('name', 'Unknown League')
                    league_id_name_map[league_id] = league_name
                    events = league.get('events', [])
                    event_ids = [event.get('id') for event in events if event.get('id')]

                    all_event_ids.extend(event_ids)

                if not all_event_ids:
                    print("没有进行中的足球赛事。")
                    return {}

                # 第二步：一次性获取所有比赛的详细信息
                params = {
                    "sportId": 29,  # 足球
                    "eventIds": ','.join(map(str, all_event_ids))
                }
                response_fixtures = requests.get(url_fixtures, params=params,
                                                 auth=HTTPBasicAuth(username, password))

                if response_fixtures.status_code == 200:
                    fixtures_data = response_fixtures.json()

                    if 'league' in fixtures_data:
                        leagues_data = fixtures_data['league']
                        result = {}

                        for league_data in leagues_data:
                            league_id = league_data.get('id', 'Unknown League ID')
                            league_name = league_data.get('name', 'Unknown League')

                            events_list = []
                            for event in league_data.get('events', []):
                                match_info = {
                                    'home_team': event.get('home', 'Unknown Home Team'),
                                    'away_team': event.get('away', 'Unknown Away Team'),
                                    'start_time': event.get('starts', 'Unknown Start Time'),
                                    'event_id': event.get('id', 'Unknown ID')
                                }
                                events_list.append(match_info)

                            # 将每个联赛下的比赛信息添加到结果中
                            result[league_id] = {
                                'league_name': league_name,
                                'events': events_list
                            }

                        return result  # 返回整理好的数据
                    else:
                        print("没有比赛的详细信息。")
                        return {}
                else:
                    print(f"获取比赛详情失败，状态码: {response_fixtures.status_code}")
                    return {}
            else:
                print("没有进行中的足球赛事。")
                return {}
        else:
            print(f"请求滚球比赛数据失败，状态码: {response_inrunning.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return {}


def get_event_details(event_ids, sport_id):
    """
    根据Event ID获取比赛详细信息。
    支持单个或多个Event ID。
    """
    url = "https://api.ps3838.com/v3/fixtures"

    # 确保event_ids是一个列表，即使是单个ID
    if isinstance(event_ids, int):
        event_ids = [event_ids]

    params = {
        "sportId": sport_id,  # 足球的运动类型ID
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


def send_data_to_server(data):
    try:
        # 将数据转换为 JSON 格式
        response = requests.post('http://localhost:8080/receive_odds_server1', json=data)
        if response.status_code == 200:
            print("1号服务器：数据已成功发送到主服务器")
        else:
            print(f"1号服务器：发送数据失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"1号服务器：发送数据时发生错误: {e}")



def getFootball_today_info_with_odds_ForClient(odds_format="Decimal"):
    """
    获取所有足球联赛的今日滚球比赛，包含每场比赛的赔率信息。
    返回包含比赛和赔率信息的完整数据结构。
    """
    url_inrunning = f"{base_url}/v2/inrunning"
    url_fixtures = f"{base_url}/v3/fixtures"
    url_odds = f"{base_url}/v3/odds"

    try:
        # 第一步：获取今日进行中的比赛信息
        response_inrunning = requests.get(url_inrunning, auth=HTTPBasicAuth(username, password))

        if response_inrunning.status_code != 200:
            print(f"请求滚球比赛数据失败，状态码: {response_inrunning.status_code}")
            return {}

        inrunning_data = response_inrunning.json()
        sports = inrunning_data.get('sports', [])
        if not sports:
            print("没有进行中的足球赛事。")
            return {}

        football_data = sports[0]
        leagues = football_data.get('leagues', [])

        # 收集所有进行中的比赛的 event_id
        all_event_ids = [
            event.get('id') for league in leagues for event in league.get('events', []) if event.get('id')
        ]

        if not all_event_ids:
            print("没有进行中的足球赛事。")
            return {}

        # 第二步：一次性获取所有比赛的详细信息
        fixtures_params = {
            "sportId": 29,  # 足球
            "eventIds": ','.join(map(str, all_event_ids))
        }
        response_fixtures = requests.get(
            url_fixtures, params=fixtures_params, auth=HTTPBasicAuth(username, password)
        )

        if response_fixtures.status_code != 200:
            print(f"获取比赛详情失败，状态码: {response_fixtures.status_code}")
            return {}

        fixtures_data = response_fixtures.json()
        leagues_data = fixtures_data.get('league', [])
        if not leagues_data:
            print("没有比赛的详细信息。")
            return {}

        # 第三步：一次性获取所有比赛的赔率信息
        odds_params = {
            "sportId": 29,
            "eventIds": ','.join(map(str, all_event_ids)),
            "oddsFormat": odds_format
        }
        response_odds = requests.get(
            url_odds, params=odds_params, auth=HTTPBasicAuth(username, password)
        )

        if response_odds.status_code != 200:
            print(f"获取赔率信息失败，状态码: {response_odds.status_code}")
            return {}

        odds_data = response_odds.json()
        odds_leagues = odds_data.get('leagues', [])

        # 创建一个字典，用于快速查找比赛的赔率信息
        odds_event_dict = {
            odds_event.get('id'): odds_event
            for odds_league in odds_leagues
            for odds_event in odds_league.get('events', [])
            if odds_event.get('id')
        }

        result = {}
        for league_data in leagues_data:
            league_id = league_data.get('id', 'Unknown League ID')
            league_name = league_data.get('name', 'Unknown League')

            events_list = []
            for event in league_data.get('events', []):
                event_id = event.get('id', 'Unknown ID')
                home_team = event.get('home', 'Unknown Home Team')
                away_team = event.get('away', 'Unknown Away Team')
                start_time = event.get('starts', 'Unknown Start Time')

                # 获取该比赛的赔率信息
                odds_info = odds_event_dict.get(event_id, {})
                periods = odds_info.get('periods', [])

                # 提取需要的赔率信息
                odds_list = []
                for period in periods:
                    period_number = period.get('number')
                    # 处理让分赔率（SPREAD）
                    for spread in period.get('spreads', []):
                        odds_list.append({
                            'betType': 'SPREAD',
                            'periodNumber': period_number,
                            'hdp': spread.get('hdp'),
                            'homeOdds': spread.get('home'),
                            'awayOdds': spread.get('away')
                        })

                    # 处理大小球赔率（TOTAL_POINTS）
                    for total in period.get('totals', []):
                        odds_list.append({
                            'betType': 'TOTAL_POINTS',
                            'periodNumber': period_number,
                            'points': total.get('points'),
                            'overOdds': total.get('over'),
                            'underOdds': total.get('under')
                        })

                    # 处理独赢赔率（MONEYLINE）
                    moneyline = period.get('moneyline', {})
                    if moneyline:
                        odds_list.append({
                            'betType': 'MONEYLINE',
                            'periodNumber': period_number,
                            'homeOdds': moneyline.get('home'),
                            'drawOdds': moneyline.get('draw'),
                            'awayOdds': moneyline.get('away')
                        })

                match_info = {
                    'event_id': event_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'start_time': start_time,
                    'odds': odds_list  # 添加赔率信息
                }
                events_list.append(match_info)

            # 将每个联赛下的比赛信息添加到结果中
            result = {
                'league_name': league_name,
                'events': events_list
            }
            print(result)
        return result  # 返回整理好的数据

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return {}


def getFootball_today_info_with_odds_ForServer(odds_format="Decimal"):
    """
    获取所有足球联赛的今日滚球比赛，包含每场比赛的赔率信息和比分数据。
    返回包含比赛、赔率和比分信息的完整数据结构。
    """
    url_inrunning = f"{base_url}/v2/inrunning"
    url_fixtures = f"{base_url}/v3/fixtures"
    url_odds = f"{base_url}/v3/odds"

    try:
        # 获取今日进行中的比赛信息
        response_inrunning = requests.get(url_inrunning, auth=HTTPBasicAuth(username, password))

        if response_inrunning.status_code != 200:
            print(f"请求滚球比赛数据失败，状态码: {response_inrunning.status_code}")
            return {}

        inrunning_data = response_inrunning.json()
        sports = inrunning_data.get('sports', [])
        if not sports:
            print("没有进行中的足球赛事。")
            return {}

        football_data = sports[0]
        leagues = football_data.get('leagues', [])

        # 收集所有进行中的比赛的 event_id
        all_event_ids = [
            event.get('id') for league in leagues for event in league.get('events', []) if event.get('id')
        ]

        if not all_event_ids:
            print("没有进行中的足球赛事。")
            return {}

        # 获取比赛详情
        fixtures_params = {
            "sportId": 29,
            "eventIds": ','.join(map(str, all_event_ids))
        }
        response_fixtures = requests.get(
            url_fixtures, params=fixtures_params, auth=HTTPBasicAuth(username, password)
        )

        if response_fixtures.status_code != 200:
            print(f"获取比赛详情失败，状态码: {response_fixtures.status_code}")
            return {}

        fixtures_data = response_fixtures.json()
        leagues_data = fixtures_data.get('league', [])
        if not leagues_data:
            print("没有比赛的详细信息。")
            return {}

        # 获取比赛赔率
        odds_params = {
            "sportId": 29,
            "eventIds": ','.join(map(str, all_event_ids)),
            "oddsFormat": odds_format
        }
        response_odds = requests.get(
            url_odds, params=odds_params, auth=HTTPBasicAuth(username, password)
        )

        if response_odds.status_code != 200:
            print(f"获取赔率信息失败，状态码: {response_odds.status_code}")
            return {}

        odds_data = response_odds.json()
        odds_leagues = odds_data.get('leagues', [])

        odds_event_dict = {
            odds_event.get('id'): odds_event
            for odds_league in odds_leagues
            for odds_event in odds_league.get('events', [])
            if odds_event.get('id')
        }

        result = {}
        for league_data in leagues_data:
            league_id = league_data.get('id', 'Unknown League ID')
            league_name = league_data.get('name', 'Unknown League')

            events_list = []
            for event in league_data.get('events', []):
                event_id = event.get('id', 'Unknown ID')
                home_team = event.get('home', 'Unknown Home Team')
                away_team = event.get('away', 'Unknown Away Team')
                start_time = event.get('starts', 'Unknown Start Time')

                # 获取赔率和比分信息
                odds_info = odds_event_dict.get(event_id, {})
                periods = odds_info.get('periods', [])
                home_score = odds_info.get('homeScore', '')
                away_score = odds_info.get('awayScore', '')

                # 提取赔率信息
                odds_list = []
                for period in periods:
                    period_number = period.get('number')
                    for spread in period.get('spreads', []):
                        odds_list.append({
                            'betType': 'SPREAD',
                            'periodNumber': period_number,
                            'hdp': spread.get('hdp'),
                            'homeOdds': spread.get('home'),
                            'awayOdds': spread.get('away')
                        })
                    for total in period.get('totals', []):
                        odds_list.append({
                            'betType': 'TOTAL_POINTS',
                            'periodNumber': period_number,
                            'points': total.get('points'),
                            'overOdds': total.get('over'),
                            'underOdds': total.get('under')
                        })
                    moneyline = period.get('moneyline', {})
                    if moneyline:
                        odds_list.append({
                            'betType': 'MONEYLINE',
                            'periodNumber': period_number,
                            'homeOdds': moneyline.get('home'),
                            'drawOdds': moneyline.get('draw'),
                            'awayOdds': moneyline.get('away')
                        })

                match_info = {
                    'event_id': event_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'start_time': start_time,
                    'home_score': home_score,
                    'away_score': away_score,
                    'odds': odds_list
                }
                events_list.append(match_info)

            result[league_id] = {
                'league_name': league_name,
                'events': events_list
            }
        return result

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return {}



def refresh_odds_every_second():
    """
    每秒刷新一次比赛赔率信息，并将数据分别保存为正常比赛和角球比赛的 CSV 文件。
    """

    def fetch_and_process_odds():
        while True:
            try:
                # 获取最新的赔率信息
                football_data = getFootball_today_info_with_odds_ForServer()

                if football_data:
                    match_count_normal = 0  # 正常比赛计数器
                    match_count_corner = 0  # 角球比赛计数器
                    all_bet_types_normal = set()  # 正常比赛的盘口类型
                    all_bet_types_corner = set()  # 角球比赛的盘口类型

                    # 分类收集所有的盘口类型
                    normal_data = []
                    corner_data = []

                    for league_id, league_info in football_data.items():
                        league_name = league_info['league_name']
                        events = league_info['events']

                        for event in events:
                            home_team = event['home_team']
                            away_team = event['away_team']
                            is_corner_match = "Corners" in league_name or "Corners" in home_team or "Corners" in away_team

                            odds_list = event.get('odds', [])
                            for odds in odds_list:
                                bet_type = odds.get('betType')
                                period_number = odds.get('periodNumber')
                                hdp = odds.get('hdp', '')
                                points = odds.get('points', '')

                                period_str = 'FT' if period_number == 0 else '1H'

                                if bet_type == 'TOTAL_POINTS' and points != '':
                                    bet_type_name = f"{bet_type}_{period_str}_{points}"
                                elif bet_type == 'SPREAD' and hdp != '':
                                    bet_type_name = f"{bet_type}_{period_str}_{hdp}"
                                elif bet_type == 'MONEYLINE':
                                    bet_type_name = f"{bet_type}_{period_str}"
                                else:
                                    continue

                                if is_corner_match:
                                    all_bet_types_corner.add(bet_type_name)
                                else:
                                    all_bet_types_normal.add(bet_type_name)

                            if is_corner_match:
                                corner_data.append((league_name, event))
                                match_count_corner += 1
                            else:
                                normal_data.append((league_name, event))
                                match_count_normal += 1

                    # 定义列名，正常比赛和角球比赛分别使用不同的盘口
                    bet_type_columns_normal = sorted(all_bet_types_normal, key=lambda x: ('1H' in x, x))
                    bet_type_columns_corner = sorted(all_bet_types_corner, key=lambda x: ('1H' in x, x))

                    columns_normal = ['league', 'match_time', 'home_team', 'away_team', 'home_score', 'away_score'] + bet_type_columns_normal
                    columns_corner = ['league', 'match_time', 'home_team', 'away_team', 'home_score', 'away_score'] + bet_type_columns_corner

                    # 正常比赛数据
                    csv_data_normal = []
                    for league_name, event in normal_data:
                        row = {column: '' for column in columns_normal}
                        row['league'] = league_name
                        row['home_team'] = event['home_team']
                        row['away_team'] = event['away_team']
                        row['match_time'] = event['start_time']
                        row['home_score'] = event.get('home_score', '')
                        row['away_score'] = event.get('away_score', '')

                        odds_list = event.get('odds', [])
                        for odds in odds_list:
                            bet_type = odds.get('betType')
                            period_number = odds.get('periodNumber')
                            hdp = odds.get('hdp', '')
                            points = odds.get('points', '')

                            home_odds = odds.get('homeOdds', '')
                            away_odds = odds.get('awayOdds', '')
                            draw_odds = odds.get('drawOdds', '')
                            over_odds = odds.get('overOdds', '')
                            under_odds = odds.get('underOdds', '')

                            period_str = 'FT' if period_number == 0 else '1H'

                            if bet_type == 'TOTAL_POINTS' and points != '':
                                bet_type_name = f"{bet_type}_{period_str}_{points}"
                                row[bet_type_name] = f"OverOdds:{over_odds}, UnderOdds:{under_odds}"
                            elif bet_type == 'SPREAD' and hdp != '':
                                bet_type_name = f"{bet_type}_{period_str}_{hdp}"
                                row[bet_type_name] = f"HomeOdds:{home_odds}, AwayOdds:{away_odds}"
                            elif bet_type == 'MONEYLINE':
                                bet_type_name = f"{bet_type}_{period_str}"
                                row[bet_type_name] = f"HomeOdds:{home_odds}, DrawOdds:{draw_odds}, AwayOdds:{away_odds}"

                        csv_data_normal.append(row)

                    # 角球比赛数据
                    csv_data_corner = []
                    for league_name, event in corner_data:
                        row = {column: '' for column in columns_corner}
                        row['league'] = league_name
                        row['home_team'] = event['home_team']
                        row['away_team'] = event['away_team']
                        row['match_time'] = event['start_time']
                        row['home_score'] = event.get('home_score', '')
                        row['away_score'] = event.get('away_score', '')

                        odds_list = event.get('odds', [])
                        for odds in odds_list:
                            bet_type = odds.get('betType')
                            period_number = odds.get('periodNumber')
                            hdp = odds.get('hdp', '')
                            points = odds.get('points', '')

                            home_odds = odds.get('homeOdds', '')
                            away_odds = odds.get('awayOdds', '')
                            over_odds = odds.get('overOdds', '')
                            under_odds = odds.get('underOdds', '')

                            period_str = 'FT' if period_number == 0 else '1H'

                            if bet_type == 'TOTAL_POINTS' and points != '':
                                bet_type_name = f"{bet_type}_{period_str}_{points}"
                                row[bet_type_name] = f"OverOdds:{over_odds}, UnderOdds:{under_odds}"
                            elif bet_type == 'SPREAD' and hdp != '':
                                bet_type_name = f"{bet_type}_{period_str}_{hdp}"
                                row[bet_type_name] = f"HomeOdds:{home_odds}, AwayOdds:{away_odds}"

                        csv_data_corner.append(row)

                    # 写入正常比赛CSV
                    with open('football_odds_normal.csv', 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=columns_normal)
                        writer.writeheader()
                        writer.writerows(csv_data_normal)

                    # 写入角球比赛CSV
                    with open('football_odds_corners.csv', 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=columns_corner)
                        writer.writeheader()
                        writer.writerows(csv_data_corner)

                    print(f"正常比赛数据已写入 football_odds_normal.csv，角球比赛数据已写入 football_odds_corners.csv。")
                else:
                    print("未获取到足球比赛数据。")

                time.sleep(1)
            except KeyboardInterrupt:
                print("停止刷新赔率信息。")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                time.sleep(1)

    refresh_thread = threading.Thread(target=fetch_and_process_odds)
    refresh_thread.daemon = True
    refresh_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("主程序已停止。")





'''
v2running()
getFootball_today_info()
get_event_details(event,29)
'''

if __name__ == "__main__":
    #get_event_details(1600614449, 29)
    #get_all_odds_and_lines(1600614978, 29, odds_format="Decimal")
    getFootball_today_info_with_odds_ForClient(odds_format="Decimal")
    refresh_odds_every_second()
