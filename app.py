from flask import Flask, request, jsonify, render_template_string
from google.cloud import storage  # 🚀 引入 GCP Storage 套件
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 偵測環境變數設定連線
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "8625")
DB_USER = os.environ.get("DB_USER", "cki101_user")
DB_PASS = os.environ.get("DB_PASSWORD", "user_password_here")
DB_NAME = os.environ.get("DB_NAME", "cki101_db")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定義 User 資料表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "age": self.age}

with app.app_context():
    db.create_all()

# 🎨 前端網頁範本（使用 Bootstrap 5 做出好看的 UI）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User 管理系統</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5" style="max-width: 800px;">
        <h2 class="mb-4 text-center text-primary">👤 User 管理作業頁面</h2>
        
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-primary text-white">✨ 新增用戶</div>
            <div class="card-body">
                <form id="userForm" class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label">姓名</label>
                        <input type="text" id="name" class="form-control" placeholder="請輸入姓名" required>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">年紀</label>
                        <input type="number" id="age" class="form-control" placeholder="年紀" required>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button type="submit" class="btn btn-success w-100">新增</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="card shadow-sm">
            <div class="card-header bg-dark text-white">📋 用戶資料清單</div>
            <div class="card-body">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>姓名</th>
                            <th>年紀</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="userTableBody">
                        </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // 頁面載入完成後自動獲取資料
        document.addEventListener('DOMContentLoaded', loadUsers);

        // 1. 檢視功能：撈取所有用戶並渲染到表格
        async function loadUsers() {
            const res = await fetch('/user?format=json');
            const users = await res.json();
            const tbody = document.getElementById('userTableBody');
            tbody.innerHTML = '';
            
            if(users.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">目前沒有任何用戶資料</td></tr>`;
                return;
            }

            users.forEach(user => {
                tbody.innerHTML += `
                    <tr>
                        <td>${user.id}</td>
                        <td><strong>${user.name}</strong></td>
                        <td>${user.age} 歲</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteUser(${user.id})">🗑️ 刪除</button>
                        </td>
                    </tr>
                `;
            });
        }

        // 2. 新增功能：送出表單
        document.getElementById('userForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('name').value;
            const age = document.getElementById('age').value;

            const res = await fetch('/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, age })
            });

            if (res.ok) {
                document.getElementById('userForm').reset();
                loadUsers(); // 重新整理列表
            } else {
                alert('新增失敗');
            }
        });

        // 3. 刪除功能
        async function deleteUser(id) {
            if (!confirm('確定要刪除這位用戶嗎？')) return;

            const res = await fetch(`/user?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                loadUsers(); // 重新整理列表
            } else {
                alert('刪除失敗');
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 🚀 /user 路由（整合網頁 UI 與 API 接口）
# ==========================================
@app.route('/user', methods=['GET', 'POST', 'DELETE'])
def manage_user():
    # 1. 查詢與檢視 (GET)
    if request.method == 'GET':
        # 如果是前端 JavaScript 或者是特定請求要資料，回傳 JSON
        if request.args.get('format') == 'json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            user_id = request.args.get('id')
            if user_id:
                user = User.query.get(user_id)
                return jsonify(user.to_dict()) if user else (jsonify({"error": "User not found"}), 404)
            return jsonify([u.to_dict() for u in User.query.all()])
        
        # 💡 預設直接在瀏覽器打網址時，回傳漂亮的操作網頁 UI
        return render_template_string(HTML_TEMPLATE)

    # 2. 新增用戶 (POST)
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data or 'age' not in data:
            return jsonify({"error": "Missing name or age"}), 400
        
        new_user = User(name=data['name'], age=int(data['age']))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully", "user": new_user.to_dict()}), 201

    # 3. 刪除用戶 (DELETE)
    elif request.method == 'DELETE':
        user_id = request.args.get('id')
        if not user_id:
            return jsonify({"error": "Missing user id"}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user_id} deleted successfully"})
# 🎨 /gcp 頁面的前端 UI 範本
GCP_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCP Cloud Storage 瀏覽器</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5" style="max-width: 800px;">
        <h2 class="mb-4 text-center text-success">☁️ GCP Cloud Storage 瀏覽器</h2>
        
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-success text-white">🔍 查詢專案儲存桶 (Buckets)</div>
            <div class="card-body">
                <form method="POST" action="/gcp" class="row g-3">
                    <div class="col-md-9">
                        <label class="form-label">GCP Project ID</label>
                        <input type="text" name="project_id" class="form-control" 
                               placeholder="例如: cki101-project-123456" 
                               value="{{ project_id }}" required>
                    </div>
                    <div class="col-md-3 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary w-100">開始查詢</button>
                    </div>
                </form>
            </div>
        </div>

        {% if error_msg %}
        <div class="alert alert-danger" role="alert">
            ❌ 錯誤原因：{{ error_msg }}
        </div>
        {% endif %}

        {% if buckets is not none %}
        <div class="card shadow-sm">
            <div class="card-header bg-dark text-white">📦 該專案下的 Buckets 清單 (共 {{ buckets|length }} 個)</div>
            <div class="card-body">
                {% if buckets|length == 0 %}
                    <p class="text-muted text-center my-3">此專案下目前沒有任何 Cloud Storage Bucket。</p>
                {% else %}
                    <ul class="list-group">
                        {% for bucket in buckets %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                🪣 <strong class="text-secondary">{{ bucket.name }}</strong>
                            </div>
                            <span class="badge bg-info text-dark">儲存級別: {{ bucket.storage_class }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# ==========================================
# 🚀 全新追加的 /gcp 路由
# ==========================================
@app.route('/gcp', methods=['GET', 'POST'])
def view_gcp_storage():
    project_id = ""
    buckets_list = None
    error_msg = None

    if request.method == 'POST':
        project_id = request.form.get('project_id', '').strip()
        
        try:
            # 💡 核心：使用標準 ADC 機制初始化 Storage Client
            # 它會自動去抓你系統註冊的憑證，並指向你輸入的 project_id
            storage_client = storage.Client(project=project_id)
            
            # 撈取該專案內的所有 buckets
            buckets = storage_client.list_buckets()
            
            # 將結果轉為 list 傳給前端
            buckets_list = [b for b in buckets]
            
        except Exception as e:
            error_msg = str(e)

    # 渲染網頁並把資料帶進去
    return render_template_string(
        GCP_TEMPLATE, 
        project_id=project_id, 
        buckets=buckets_list, 
        error_msg=error_msg
    )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
