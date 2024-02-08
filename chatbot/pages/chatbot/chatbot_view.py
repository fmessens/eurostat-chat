import json

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

# import components
from chatbot.components.input import render_chat_input
from chatbot.pages.queryapp.queryview import layout


# define layout
chatbot_layout = html.Div(
    html.Div(id="display-conversation"),
    style={
        "overflow-y": "auto",
        "display": "flex",
        "height": "calc(90vh - 132px)",
        "flex-direction": "column-reverse",
    },
)


def render_chatbot():
    return html.Div(
        [
            html.Br(),
            dcc.Store(id="store-bot-conversation",
                      data=json.dumps([])),
            dcc.Store(id="store-human-conversation",
                      data=json.dumps([])),
            dbc.Container(
                fluid=True,
                children=[
                    dbc.Row(
                        [
                            dbc.Col(width=1),
                            dbc.Col(
                                width=10,
                                children=dbc.Card(
                                    [
                                        dbc.CardBody([
                                            chatbot_layout,
                                            html.Div(render_chat_input(),
                                                     style={'margin-left': '70px',
                                                            'margin-right': '70px',
                                                            'margin-bottom': '20px'}),
                                            html.Br(),
                                            html.Br(),
                                            html.Br(),
                                            dcc.Loading(id="loading-component", 
                                                        type="circle",
                                                        children=html.Div(id="loading-output-1")),
                                        ])

                                    ],
                                    style={'border-radius': 25, 'background': '#FFFFFF', 'border': '0px solid'}
                                )
                            ),
                            dbc.Col(width=1),
                        layout]
                    )
                ]
            ),
        ],
    )