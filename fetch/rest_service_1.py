import requests
from datetime import datetime
import pytz
from dateutil import parser
from flask import Flask, jsonify
import os
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

username = "GA1A711D01"
password = "dddd1111"
# 定义排除关键词列表
EXCLUDE_KEYWORDS = ['Corners', 'Bookings']

def fetch_fixtures():
    """
    从API获取足球赛事数据。

    返回:
        dict: API返回的JSON数据，如果请求失败或解析失败，返回None。
    """
    base_url = "https://api.ps3838.com"
    endpoint = "/v3/fixtures"
    url = f"{base_url}{endpoint}"
    params = {
        'sportId': 29  # 足球
    }

    try:
        response = requests.get(url, auth=(username, password), params=params)
        response.raise_for_status()
        logging.info("成功获取API数据。")
    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败: {e}")
        return None

    try:
        data = response.json()

        logging.info("成功解析API的JSON响应。")
    except requests.exceptions.JSONDecodeError:
        logging.error("无法解析API的JSON响应。")
        return None

    return data

def contains_exclude_keywords(text):
    """
    检查文本是否包含任何排除关键词。

    Args:
        text (str): 要检查的文本。

    Returns:
        bool: 如果包含任意排除关键词，返回True，否则返回False。
    """
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text.lower():
            return True
    return False


def get_today_unsettled_fixtures():
    """
    获取今日未结算的足球赛事信息，根据GMT-4时间。

    排除联赛名称或主客队名称中包含 "Corners" 或 "Bookings" 的比赛。

    返回:
        list: 今日未结算的比赛列表，每个元素包含联赛名称、主队、客队名称、开赛时间及状态。
        int: 今日比赛的数量。
    """
    data = fetch_fixtures()
    if not data:
        return [], 0

    leagues = data.get('league')
    if not leagues:
        logging.warning("API响应中没有 'league' 键或 'league' 为空。")
        return [], 0

    if not isinstance(leagues, list):
        logging.error("'league' 键的内容不是列表。")
        return [], 0

    # 定义固定的GMT-4时区
    gmt4 = pytz.FixedOffset(-240)  # GMT-4对应的偏移量为-240分钟

    # 获取当前日期（GMT-4时间）
    now_gmt4 = datetime.now(gmt4)
    today_gmt4 = now_gmt4.date()

    logging.info(f"当前GMT-4日期: {today_gmt4}")

    fixtures_today = []
    seen_fixtures = set()  # 用于跟踪已见过的比赛

    for league in leagues:
        league_name = league.get('name', '未知联赛')
        events = league.get('events', [])

        if not events:
            #logging.info(f"联赛 '{league_name}' 中没有找到赛事。")
            continue

        #logging.info(f"正在处理联赛: {league_name}，共有 {len(events)} 场比赛")

        for event in events:
            starts = event.get('starts')
            home_team = event.get('home', '未知主队')
            away_team = event.get('away', '未知客队')

            if not starts:
                #logging.warning(f"赛事 '{home_team} vs {away_team}' 缺少开始时间，跳过。")
                continue

            try:
                # 解析比赛开始时间
                fixture_datetime = parser.isoparse(starts)
                if fixture_datetime.tzinfo is None:
                    # 如果原始时间没有时区信息，假设为UTC
                    fixture_datetime = fixture_datetime.replace(tzinfo=pytz.UTC)
                # 转换为GMT-4时间
                fixture_datetime_gmt4 = fixture_datetime.astimezone(gmt4)
                fixture_date_gmt4 = fixture_datetime_gmt4.date()
            except (ValueError, TypeError) as ve:
                #logging.error(f"日期解析错误: {ve}, 赛事 '{home_team} vs {away_team}' 跳过。")
                continue

            # 比较日期是否为今天的GMT-4时间
            if fixture_date_gmt4 == today_gmt4:
                # 排除包含 "Corners" 或 "Bookings" 的比赛
                if (contains_exclude_keywords(league_name) or
                    contains_exclude_keywords(home_team) or
                    contains_exclude_keywords(away_team)):
                    #logging.info(f"赛事 '{home_team} vs {away_team}' 包含排除关键词，跳过。")
                    continue

                # 定义比赛的唯一标识
                fixture_key = (league_name.lower(), home_team.lower(), away_team.lower())

                if fixture_key in seen_fixtures:
                    #logging.info(f"发现重复赛事: {league_name}: {home_team} vs {away_team}，跳过。")
                    continue  # 跳过重复的比赛



                # 添加到今日未结算的比赛列表
                fixture = {
                    'league': league_name,
                    'home_team': home_team,
                    'away_team': away_team,
                    'time': fixture_datetime_gmt4.strftime('%H:%M'),  # 只保留时分

                }
                fixtures_today.append(fixture)
                seen_fixtures.add(fixture_key)  # 标记为已见过

                # 输出原始比赛数据到控制台
                #print("原始赛事数据:", event)

                #logging.info(f"匹配今日赛事: {league_name}: {home_team} vs {away_team}, 开赛时间: {fixture_datetime_gmt4.strftime('%H:%M')}")
            else:
                #logging.info(f"赛事日期 ({fixture_date_gmt4}) 不匹配今日日期 ({today_gmt4}), 跳过。")
                pass

    return fixtures_today, len(fixtures_today)



@app.route('/today_fixtures', methods=['GET'])
def today_fixtures():
    """
    API端点，获取今日未结算的足球赛事信息。

    返回:
        JSON: 包含比赛数量和比赛列表。
    """
    fixtures, count = get_today_unsettled_fixtures()
    return jsonify({
        'dataSource': 1,
        'count': count,
        'fixtures': fixtures
    })

if __name__ == "__main__":
    # 运行Flask应用，监听所有IP，端口5000
    app.run(host='0.0.0.0', port=5000)
