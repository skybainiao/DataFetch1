from flask import Flask, jsonify
from fetch_1_net import getFootball_today_info_with_odds_ForClient  # 替换为你的实际文件名和方法

app = Flask(__name__)


@app.route('/matches', methods=['GET'])
def get_matches():
    """
    获取所有今日足球比赛和赔率信息，包括联赛名称。
    """
    try:
        # 从原始方法获取数据
        data = getFootball_today_info_with_odds_ForClient()

        # 确保返回的数据结构包含联赛名称和比赛数据
        if data:
            return jsonify(data), 200
        else:
            return jsonify({"message": "No match data available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 运行在本地所有IP，端口5000
