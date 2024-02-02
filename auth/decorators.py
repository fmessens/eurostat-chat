from flask import redirect, session, url_for, jsonify, request, current_app
from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def requires_auth(f):
    """
    Use on routes that require a valid session, otherwise it aborts with a 403
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user') is None:
            # get the current url in the session object
            session['after_auth_redirect'] = request.url
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated


def api_guard(f):
    """
    Use on API routes that require a valid JWT, otherwise it aborts with a 403
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'Missing token'}), 401

        try:
            token = auth_header.split(' ')[1]
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(token)
        except BadSignature:
            return jsonify({'message': 'Invalid token'}), 401
        except SignatureExpired:
            return jsonify({'message': 'Expired token'}), 401

        session['user'] = {'userinfo': {'aud': data['uid']}}
        return f(*args, **kwargs)

    return decorated