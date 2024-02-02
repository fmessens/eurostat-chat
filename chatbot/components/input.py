import dash_bootstrap_components as dbc
from dash import html

def render_chat_input():
    chat_input = dbc.InputGroup(
        children=[
            dbc.Input(id="user-input", placeholder="Send a message...", type="text"),
            html.Button(id="submit", children=">", className="btn btn-block btn-primary mb-3",
                        style={'background-color': '#ff9800'}),
        ],
    )
    return chat_input