import json
import os
from datetime import time

import requests
from requests.auth import HTTPBasicAuth
import time
import csv
import threading
import pandas as pd
from datetime import datetime

username = "E01AA0NDM1"
password = "dddd1111"
base_url = "https://api.ps3838.com"


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


def process_and_save_data(football_data, normal_csv, corner_csv):
    """
    处理足球数据并保存到CSV文件中。
    """
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

    columns_normal = ['league', 'match_time', 'home_team', 'away_team', 'home_score',
                      'away_score'] + bet_type_columns_normal
    columns_corner = ['league', 'match_time', 'home_team', 'away_team', 'home_score',
                      'away_score'] + bet_type_columns_corner

    send_data(normal_data, "http://localhost:8080/receive_odds_server1")
    send_data(corner_data, "http://localhost:8080/receive_corner_odds")
    save_to_csv(normal_data, columns_normal, normal_csv)
    save_to_csv(corner_data, columns_corner, corner_csv)


def save_to_csv(data, columns, filename, max_saves=12):
    """
    保存数据到CSV文件，每次写入数据算作一次保存。
    动态更新字段，确保文件中最多保留最近 max_saves 次写入数据。
    """
    csv_data = []

    # 添加时间戳行，标记此次写入
    timestamp_row = {column: '' for column in columns}
    timestamp_row['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csv_data.append(timestamp_row)

    # 动态更新 columns，确保所有字段都包括
    for league_name, event in data:
        row = {column: '' for column in columns}
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

            # 动态添加新字段到 columns
            if bet_type_name not in columns:
                columns.append(bet_type_name)

        csv_data.append(row)

    # 读取现有文件数据
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as csvfile:
            existing_data = list(csv.DictReader(csvfile))

        # 动态更新 columns based on existing data
        for row in existing_data:
            for key in row.keys():
                if key not in columns:
                    columns.append(key)

        # 分离现有数据中的写入次数
        saves = []
        current_save = []
        for row in existing_data:
            if row['Timestamp']:  # 以时间戳行为分隔标志
                if current_save:
                    saves.append(current_save)
                current_save = [row]
            else:
                current_save.append(row)
        if current_save:
            saves.append(current_save)

        # 只保留最近 max_saves 次写入数据
        if len(saves) >= max_saves:
            saves = saves[-(max_saves - 1):]  # 保留最近 max_saves-1 次

        # 添加新的写入
        saves.append(csv_data)

        # 整合所有保存的数据
        all_data = [row for save in saves for row in save]
    else:
        all_data = csv_data

    # 写入数据到文件
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_data)


def refresh_odds_every_second(t):
    """
    每秒刷新一次比赛赔率信息，并将数据分别保存为正常比赛和角球比赛的 CSV 文件。
    """
    print("1网服务器已启动")

    def fetch_and_process_odds():
        while True:
            try:
                football_data = getFootball_today_info_with_odds_ForServer()
                if football_data:
                    process_and_save_data(
                        football_data,
                        'football_odds_normal.csv',
                        'football_odds_corners.csv'
                    )
                else:
                    print("目前没有滚球赛事。")
                time.sleep(t)
            except KeyboardInterrupt:
                print("停止刷新赔率信息。")
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
        print("主程序已停止。")


def send_data(data, server_url):
    """
    将处理后的足球数据发送到Java服务器。
    :param data: 处理后的数据列表（normal_data） (列表中的元素是元组 (league_name, event))
    :param server_url: Java服务器的URL
    """
    formatted_data = [
        {
            "leagueName": league_name,  # 从元组中解包联赛名称
            "eventId": event['event_id'],
            "matchTime": event['start_time'],
            "homeTeam": event['home_team'],
            "awayTeam": event['away_team'],
            "homeScore": event.get('home_score', 0),
            "awayScore": event.get('away_score', 0),
            "odds": [odds for odds in event.get('odds', [])]  # 确保odds为数组格式
        }
        for league_name, event in data  # data是一个包含 (league_name, event) 元组的列表
    ]

    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(server_url, data=json.dumps(formatted_data), headers=headers)

        if response.status_code == 200:
            #print("数据成功发送到Java服务器:", response.json())
            pass
        else:
            print(f"发送数据失败，状态码: {response.status_code}, 响应: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"发送数据时发生错误: {e}")
    except json.JSONDecodeError as e:
        print(f"解析服务器响应时发生错误: {e}")


if __name__ == "__main__":
    refresh_odds_every_second(0.8)
