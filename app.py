import os

from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

from auth.views import auth_bp
from chatbot.chatapp import get_chatapp
from chatbot_app import chatbot_blueprint

def page_not_found(e):
    return render_template('404.html'), 404

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.register_blueprint(auth_bp, url_prefix='/')

chatapp = get_chatapp(app, '/chatbot/')

chatbot_bp = chatbot_blueprint(chatapp.index())
app.register_blueprint(chatbot_bp, url_prefix='/')

if __name__ == "__main__":
    app.run(debug=True, port=5001)