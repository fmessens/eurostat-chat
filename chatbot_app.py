from flask import render_template, render_template_string, session, Blueprint

from auth.decorators import requires_auth

def chatbot_blueprint(chatapp_index):
    chatbot_bp = Blueprint('webapp', __name__, template_folder="templates")
    @chatbot_bp.route("/account")
    @requires_auth
    def account():
        user = session.get('user').get("userinfo")
        user['uid'] = user['aud']
        email = user['email']
        username = user['name']
        is_authenticated = True
        return render_template("account.html",
                                username=username,
                                email=email,
                                is_authenticated=is_authenticated)

    @chatbot_bp.route("/chat")
    @requires_auth
    def chatbotpage():
        user = session.get('user').get("userinfo")
        user['uid'] = user['aud']
        strindex = chatapp_index
        return render_template_string(strindex,
                                    username=user['name'],
                                    is_authenticated=True)
    return chatbot_bp