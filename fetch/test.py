import websocket
import json

ws = websocket.WebSocket()
ws.connect("ws://localhost:8080/data-stream")

# 发送有效 JSON 数据
data = {"message": "Test"}
ws.send(json.dumps(data))  # 使用 json.dumps 将数据序列化为 JSON 格式
print("Message sent.")
ws.close()
