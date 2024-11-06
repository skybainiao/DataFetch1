from flask import Flask, jsonify
from fetch.fetch_1_net import get_all_sports, get_football_leagues, get_live_league_fixtures, get_live_event_details, get_leagues_for_all_sports

# 初始化 Flask 应用程序
app = Flask(__name__)

@app.route('/sports', methods=['GET'])
def sports():
    return jsonify(get_all_sports())

@app.route('/leagues', methods=['GET'])
def all_leagues():
    return jsonify(get_leagues_for_all_sports())

@app.route('/football/leagues', methods=['GET'])
def football_leagues():
    return jsonify(get_football_leagues())

@app.route('/football/leagues/<int:league_id>/fixtures', methods=['GET'])
def live_fixtures(league_id):
    return jsonify(get_live_league_fixtures(league_id))

@app.route('/football/leagues/<int:league_id>/events/<int:event_id>', methods=['GET'])
def live_event_details(league_id, event_id):
    return jsonify(get_live_event_details(league_id, event_id))



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
