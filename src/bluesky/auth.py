from atproto import Client

_session = None

def authenticate(username, app_password):
    global _session
    _session = Client()
    _session.login(username, app_password)
    return _session.com_atproto_server_create_session.data.get("accessJwt")

def get_access_token():
    if not _session:
        raise RuntimeError("Not authenticated")
    return _session.com_atproto_server_create_session.data.get("accessJwt")

def refresh_access_token(refresh_token):
    if not _session:
        raise RuntimeError("Not authenticated")
    response = _session.com_atproto_server_refresh_session(refresh_token=refresh_token)
    return response.data.get("accessJwt")

def logout():
    global _session
    _session = None