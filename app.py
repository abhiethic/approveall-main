from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'AcceptronBot - Auto Approve Bot is Running!'

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'auto-approve-bot'}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
