import dash_bootstrap_components as dbc
from dash import html, dcc

def render_chat_input():
    chat_input = dbc.InputGroup(
        children=[
            dbc.Input(id="user-input", placeholder="Send a message...", type="text"),
            html.Div(
                    children=[
                        html.Button(id="submit", children=">", 
                                    className="btn btn-block btn-primary mb-3", 
                                    style={'background-color': '#ff9800'}),
                        html.Br(),
                        dcc.Checklist(id='prompt-chain',
                                            options=[' Activate prompt chain (no chat history)'],
                                            value=[' Activate prompt chain (no chat history)'],
                                            style={'font-size': '30px'})
                        ],
                            
                    )
                ],
            )
    return chat_input