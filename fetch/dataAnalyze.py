import json
import os
import requests
from requests.auth import HTTPBasicAuth
import time
import csv
import threading
import pandas as pd
from datetime import datetime
from collections import defaultdict, deque

username = "GA1A711D02"
password = "dddd1111"
base_url = "https://api.ps3838.com"

# 全局数据结构：用于存储赔率历史数据 (event_id, bet_type_name) -> { "history": deque, "last_alert_time": float }
odds_history = defaultdict(lambda: {
    "history": deque(maxlen=10),
    "last_alert_time": None
})

def getFootball_today_info_with_odds_ForServer(odds_format="Malay"):
    url_inrunning = f"{base_url}/v2/inrunning"
    url_fixtures = f"{base_url}/v3/fixtures"
    url_odds = f"{base_url}/v3/odds"

    try:
        response_inrunning = requests.get(url_inrunning, auth=HTTPBasicAuth(username, password))
        if response_inrunning.status_code != 200:
            return {}

        inrunning_data = response_inrunning.json()
        sports = inrunning_data.get('sports', [])
        if not sports:
            return {}

        football_data = sports[0]
        leagues = football_data.get('leagues', [])
        all_event_ids = [
            event.get('id') for league in leagues for event in league.get('events', []) if event.get('id')
        ]

        if not all_event_ids:
            return {}

        fixtures_params = {
            "sportId": 29,
            "eventIds": ','.join(map(str, all_event_ids))
        }
        response_fixtures = requests.get(
            url_fixtures, params=fixtures_params, auth=HTTPBasicAuth(username, password)
        )

        if response_fixtures.status_code != 200:
            return {}

        fixtures_data = response_fixtures.json()
        leagues_data = fixtures_data.get('league', [])
        if not leagues_data:
            return {}

        odds_params = {
            "sportId": 29,
            "eventIds": ','.join(map(str, all_event_ids)),
            "oddsFormat": odds_format
        }
        response_odds = requests.get(
            url_odds, params=odds_params, auth=HTTPBasicAuth(username, password)
        )

        if response_odds.status_code != 200:
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

                odds_info = odds_event_dict.get(event_id, {})
                periods = odds_info.get('periods', [])
                home_score = odds_info.get('homeScore', '')
                away_score = odds_info.get('awayScore', '')

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

    except requests.exceptions.RequestException:
        return {}


def process_and_save_data(football_data, normal_csv, corner_csv):
    match_count_normal = 0
    match_count_corner = 0
    all_bet_types_normal = set()
    all_bet_types_corner = set()

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

    bet_type_columns_normal = sorted(all_bet_types_normal, key=lambda x: ('1H' in x, x))
    bet_type_columns_corner = sorted(all_bet_types_corner, key=lambda x: ('1H' in x, x))

    columns_normal = ['Timestamp', 'event_id', 'league', 'match_time', 'home_team', 'away_team', 'home_score',
                      'away_score'] + bet_type_columns_normal
    columns_corner = ['Timestamp', 'event_id', 'league', 'match_time', 'home_team', 'away_team', 'home_score',
                      'away_score'] + bet_type_columns_corner

    save_to_csv(normal_data, columns_normal, normal_csv)
    save_to_csv(corner_data, columns_corner, corner_csv)


def save_to_csv(data, columns, filename):
    csv_data = []
    timestamp_row = {column: '' for column in columns}
    timestamp_row['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csv_data.append(timestamp_row)

    for league_name, event in data:
        row = {column: '' for column in columns}
        row['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row['event_id'] = event['event_id']
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

        csv_data.append(row)

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(csv_data)


def monitor_odds(football_data):
    """
    监控所有比赛的所有盘口所有赔率。
    不再限定特定 event_id，而是对获取到的所有 event_id 全部监控。
    """

    now_ts = time.time()

    # 遍历所有联赛与比赛
    for league_id, league_info in football_data.items():
        for event in league_info['events']:
            event_id = event['event_id']
            odds_list = event.get('odds', [])
            if not odds_list:
                # 如果该比赛没有赔率数据，继续下一个比赛
                continue

            # 对当前比赛的所有赔率进行记录并检查
            for odds in odds_list:
                bet_type = odds.get('betType')
                period_number = odds.get('periodNumber', '')
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
                    # 不符合这几类的盘口目前不处理
                    continue

                home_odds = odds.get('homeOdds')
                draw_odds = odds.get('drawOdds')
                away_odds = odds.get('awayOdds')
                over_odds = odds.get('overOdds')
                under_odds = odds.get('underOdds')

                # 加入历史记录
                odds_history[(event_id, bet_type_name)]["history"].append(
                    (now_ts, home_odds, draw_odds, away_odds, over_odds, under_odds)
                )

                # 假设阈值2点位作为示例，可自行调整
                check_and_alert(event_id, bet_type_name, time_window=10, threshold=2)


def check_and_alert(event_id, bet_type_name, time_window, threshold):
    """
    与之前逻辑相同：对TOTAL_POINTS, SPREAD, MONEYLINE分别检查其对应的赔率字段，
    如果发生正向涨幅且超过threshold的点位变化，则告警。

    点位 = (当前赔率 - 过去赔率)*100
    当当前赔率 > 过去赔率且点位 > threshold时告警。

    告警信息中输出具体的赔率名称和从旧值到新值的变化情况。
    """
    data = odds_history[(event_id, bet_type_name)]
    history = data["history"]

    if len(history) < 2:
        return

    (current_time, current_home_odds, current_draw_odds,
     current_away_odds, current_over_odds, current_under_odds) = history[-1]

    # 找 time_window秒前的数据点
    old_index = None
    for i in range(len(history) - 1, -1, -1):
        if current_time - history[i][0] >= time_window:
            old_index = i
            break

    if old_index is None:
        return

    (old_time, old_home_odds, old_draw_odds,
     old_away_odds, old_over_odds, old_under_odds) = history[old_index]

    # 解析盘口类型
    bet_info = bet_type_name.split('_')
    bet_type = bet_info[0]  # TOTAL_POINTS, SPREAD, MONEYLINE

    def check_and_alert_single_odds(odds_name, old_value, new_value):
        if old_value is None or new_value is None:
            return
        if new_value > old_value:
            diff_points = (new_value - old_value) * 100
            if diff_points > threshold:
                now = time.time()
                if data["last_alert_time"] is None or (now - data["last_alert_time"] > 300):
                    print(f"[告警] {time_window}秒内涨幅{diff_points:.2f}个点位 "
                          f"(Event {event_id}, {bet_type_name}, {odds_name}从{old_value}涨到了{new_value})")
                    data["last_alert_time"] = now

    if bet_type == "TOTAL_POINTS":
        check_and_alert_single_odds("OverOdds", old_over_odds, current_over_odds)
        check_and_alert_single_odds("UnderOdds", old_under_odds, current_under_odds)
    elif bet_type == "SPREAD":
        check_and_alert_single_odds("HomeOdds", old_home_odds, current_home_odds)
        check_and_alert_single_odds("AwayOdds", old_away_odds, current_away_odds)
    elif bet_type == "MONEYLINE":
        check_and_alert_single_odds("HomeOdds", old_home_odds, current_home_odds)
        check_and_alert_single_odds("DrawOdds", old_draw_odds, current_draw_odds)
        check_and_alert_single_odds("AwayOdds", old_away_odds, current_away_odds)
    else:
        # 未知类型可忽略或扩展
        pass






def refresh_odds_every_second(t):
    def fetch_and_process_odds():
        print('监控模块已启动')
        while True:
            try:
                football_data = getFootball_today_info_with_odds_ForServer()
                if football_data:
                    process_and_save_data(
                        football_data,
                        'ft_normal.csv',
                        'ft_corners.csv'
                    )
                    monitor_odds(football_data)
                else:
                    time.sleep(t)
                    continue
                time.sleep(t)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"发生错误: {e}")
                time.sleep(t)

    refresh_thread = threading.Thread(target=fetch_and_process_odds)
    refresh_thread.daemon = True
    refresh_thread.start()

    try:
        while True:
            time.sleep(t)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    refresh_odds_every_second(1)
