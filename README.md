项目名称
足球比赛和赔率信息获取工具

项目简介
本项目是一个使用 Python 编写的工具，用于获取所有足球联赛的今日滚球比赛信息，并包含每场比赛的详细赔率数据。该工具可以每秒刷新一次赔率信息，方便用户实时获取最新数据。

功能特点
获取今日进行中的足球比赛信息：包括联赛名称、比赛双方、开始时间等。
获取每场比赛的赔率信息：涵盖让分、大小球、独赢等多种赔率类型。
数据整合：将比赛信息和赔率信息整合在一起，方便后续处理或发送给其他服务器。
实时刷新：支持每秒刷新一次赔率信息，保证数据的实时性。
环境依赖
Python 3.6 及以上版本
需要安装的 Python 库：
requests：用于发送 HTTP 请求
安装和运行
1. 克隆或下载项目代码
bash
Copy code
git clone https://github.com/yourusername/yourrepository.git
2. 安装依赖库
使用 pip 安装所需的 Python 库：

bash
Copy code
pip install requests
3. 配置参数
在代码中，您需要配置以下参数：

base_url：API 的基础 URL
username 和 password：用于 API 认证的用户名和密码
确保这些参数已正确配置，以便程序能够正常运行。

4. 运行程序
在终端中执行以下命令：

bash
Copy code
python your_script_name.py
程序将开始运行，并每秒刷新一次赔率信息。

代码结构
getFootball_today_info_with_odds_ForServer(odds_format="Decimal")：获取今日足球比赛和赔率信息的主要方法，返回包含比赛和赔率信息的完整数据结构。
refresh_odds_every_second()：每秒刷新一次赔率信息的方法，使用多线程实现，不会阻塞主线程。
主程序调用 refresh_odds_every_second()，开始实时获取数据。
使用说明
获取比赛和赔率信息：调用 getFootball_today_info_with_odds_ForServer() 方法，获取包含所有比赛和赔率信息的字典。
打印数据：在方法外部，可以遍历返回的数据结构，并按照需要的格式打印到控制台。
实时刷新数据：调用 refresh_odds_every_second() 方法，程序将每秒刷新一次数据。
注意事项
API 使用政策：在频繁请求数据之前，请确保您已了解并遵守 API 提供商的使用政策，避免因过于频繁的请求而被限制或封禁。
资源消耗：每秒请求一次数据可能会消耗较多的系统资源和网络带宽，请确保您的系统能够承受这种负载。
错误处理：代码中已添加基本的错误处理，但在实际使用中，建议添加更完善的日志记录和异常处理机制。
合法合规：请确保您的使用行为符合所在国家和地区的法律法规。
许可证
MIT License
