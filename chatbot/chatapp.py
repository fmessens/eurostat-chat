from dash.dependencies import Input, Output
from dash import dcc, html, DiskcacheManager
import dash
import diskcache

# import pages
from chatbot.pages.chatbot.chatbot_view import render_chatbot
from chatbot.pages.chatbot.chatbot_controller import init_callbacks
from chatbot.pages.queryapp.querycontroller import init_query_callb
from chatbot.pages.page_not_found import page_not_found



def get_chatapp(flaskapp, url_base_pathname):
    """
    :param flaskapp: flask app
    :param url_base_pathname: url base pathname
    :return: dash app
    """
    cache = diskcache.Cache("./cache")
    long_callback_manager = DiskcacheManager(cache)
    dash_app = dash.Dash(
        server=flaskapp,
        routes_pathname_prefix=url_base_pathname,
        index_string=open('templates/dash_layout_t.html', 'r').read(),
        assets_folder='static',
        long_callback_manager = long_callback_manager
    )
    dash_app.layout = render_chatbot()
    init_callbacks(dash_app)
    init_query_callb(dash_app)
    return dash_app