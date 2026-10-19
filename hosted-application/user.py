# Eben Taljaard 

import hashlib
from flask import Flask, flash, make_response, redirect, render_template_string, request, url_for, jsonify
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user

#CERT = '/app/certs/cert.pem'
#KEY = '/app/certs/key.pem'

CERT = '/home/user/Desktop/host/certs/cert.pem'
KEY = '/home/user/Desktop/host/certs/key.pem'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-this'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Global state for background worker coordination
PROC_TRIGGERED = False
ACTIVE_SESSION_HASH = None

itemlines = [
    "101 18V Cordless Drill 2 89.99",
    "102 Painter Brick Wall 2 HRS", 
    "103 6-inch Wood Clamp 4 12.50",
    "104 Hedge Triming Summer 3 HRS",
    "105 Carpenter's Hammer 1 19.99"
]

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'User':
        return User('User')
    return None

LOGIN_TEMPLATE = '''
<!doctype html>
<html>
  <head><title>Login</title></head>
  <body>
    <h2>Login Page (User / Password)</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <p style="color: red;">{{ messages[0] }}</p>
      {% endif %}
    {% endwith %}
    <form method="POST">
      Username: <input type="text" name="username"><br><br>
      Password: <input type="password" name="password"><br><br>
      <input type="submit" value="Log In">
    </form>
  </body>
</html>
'''

SUCCESS_TEMPLATE = '''
<!doctype html>
<html>
  <head><title>Success</title></head>
  <body>
    <h2>Logged in successfully as {{ current_user.id }}!</h2>
    <p>Check your server terminal to see the session cookie value.</p>
    <p><a href="{{ itemlines_url }}">View Dynamic Itemlines Endpoint</a></p>
    
    <hr>
    <h3>Trigger Background Processing</h3>
    {% if triggered %}
      <p style="color: green; font-weight: bold;">[✓] Processing trigger signal sent to proc.py workers!</p>
    {% else %}
      <form action="{{ url_for('trigger_proc') }}" method="POST">
        <button type="submit" style="padding: 10px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Trigger proc.py Execution
        </button>
      </form>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('logout') }}">Log Out</a></p>
  </body>
</html>
'''

def get_session_md4():
    session_cookie = request.cookies.get('session')
    if not session_cookie:
        return None
    return hashlib.sha256(session_cookie.encode('utf-8')).hexdigest()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'User' and password == 'Password':
            user = User('User')
            login_user(user)
            
            session_cookie = request.cookies.get('session')
            print("\n--- SUCCESSFUL LOGIN ---")
            print(f"Session Cookie Value: {session_cookie}\n")
            
            return redirect(url_for('success'))
        else:
            flash('Invalid username or password')
            
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/success')
@login_required
def success():
    md4_hash = get_session_md4()
    itemlines_url = f"/itemlines/{md4_hash}" if md4_hash else "#"
    
    resp = make_response(render_template_string(
        SUCCESS_TEMPLATE, 
        itemlines_url=itemlines_url,
        triggered=PROC_TRIGGERED
    ))
    return resp

@app.route('/trigger-proc', methods=['POST'])
@login_required
def trigger_proc():
    """Sets trigger flag and captures the logged-in session hash for background workers."""
    global PROC_TRIGGERED, ACTIVE_SESSION_HASH
    PROC_TRIGGERED = True
    ACTIVE_SESSION_HASH = get_session_md4()
    print(f"\n[!] Webmaster triggered execution. Active Session Hash: {ACTIVE_SESSION_HASH}\n")
    return redirect(url_for('success'))

@app.route('/check-trigger', methods=['GET'])
def check_trigger():
    """Endpoint polled by proc.py workers to wait for button event."""
    return jsonify({"triggered": PROC_TRIGGERED})

@app.route('/get-hash', methods=['GET'])
def get_hash():
    """Endpoint queried by proc.py to retrieve session hash captured during trigger."""
    global ACTIVE_SESSION_HASH
    if not ACTIVE_SESSION_HASH:
        return "NO_ACTIVE_SESSION", 401, {'Content-Type': 'text/plain'}
    
    return ACTIVE_SESSION_HASH, 200, {'Content-Type': 'text/plain'}

@app.route('/itemlines/<md4_hash>', methods=['GET'])
def get_itemlines(md4_hash):
    global ACTIVE_SESSION_HASH
    
    # Validates either current session cookie or active captured session hash
    current_md4 = get_session_md4() or ACTIVE_SESSION_HASH
    
    if not current_md4 or md4_hash != current_md4:
        return "Unauthorized hash endpoint", 403

    response_body = "\n".join([f"<custom>{line}</custom>" for line in itemlines])
    return response_body, 200, {'Content-Type': 'text/plain'}

@app.route('/logout')
@login_required
def logout():
    global PROC_TRIGGERED, ACTIVE_SESSION_HASH
    PROC_TRIGGERED = False
    ACTIVE_SESSION_HASH = None
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, debug=True, ssl_context=(CERT, KEY))