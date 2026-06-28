from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "我是功能一"

if __name__ == '__main__':
    # 這裡的 port 設為 5000，host='0.0.0.0' 確保 Docker 容器外可以訪問
    app.run(host='0.0.0.0', port=5000)