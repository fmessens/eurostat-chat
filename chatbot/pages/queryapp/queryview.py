import dash
from dash import dcc, html, dash_table
import dash_ace

layout = html.Div([
                dcc.Download(id="download-dataframe-csv"),
                html.H1("Query editor"),
                dash_ace.DashAceEditor(
                        id='query-input',
                        value='',
                        placeholder='Enter SQL query here',
                        style={'width': '100%', 'height': '300px'},
                        mode='sql',  # Enable SQL syntax highlighting
                        theme='github'  # Set the color theme
                    ),
                dcc.Loading(type="dot", id="loading"),
                html.Button('Run Query', id='run-query-button', 
                            className='btn btn-block btn-primary mb-3', 
                            n_clicks=0),
                html.Div(id='query-output',
                         children=[dash_table.DataTable(id='query-table'),
                                   dcc.Dropdown(id='save-table-dropdown',
                                                options=[],
                                                style={'display': 'block'}),
                                   dcc.Input(id='save-table-name', type='text', 
                                             placeholder='Enter table name'),
                                   html.Button('Save table', id='save-table-btn',
                                               className='btn btn-block btn-primary mb-3',
                                               disabled=True)],
                        style={'display': 'none'}),
                html.Div(id='query-output-message')
            ])