import dash
from dash import dcc, html, Input, Output, dash_table, State
from dash.exceptions import PreventUpdate
import pandas as pd
from flask import session
from google.cloud import bigquery
import urllib

from auth.decorators import requires_auth


def init_query_callb(app):
    @app.callback(
        Output('downl-table-btn', 'disabled'),
        Input('downl-table-dropdown', 'value'),
        Input('downl-table-name', 'value'),
    )
    def update_downl_table_btn(org, name):
        if (org is not None and 
            name is not None
            and name != ''
            and org != ''):
            return False
        else:
            return True
    
    @app.callback(
        Output('query-output-message', 'children'),
        Output("download-dataframe-csv", "data"),
        Output("download-dataframe-csv", "filename"),
        Input('downl-table-btn', 'n_clicks'),
        Input('downl-table-name', 'value'),
        State('query-table', 'derived_virtual_data'),
        prevent_initial_call=True
    )
    @requires_auth
    def downl_table(n_clicks, data, table_name):
        if n_clicks == 0:
            raise PreventUpdate
        df = pd.DataFrame(data)
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return f'File downloaded', csv_string, f'{table_name}.csv'



    
    # Callback to execute SQL query and update output
    @app.callback(
        Output('query-output', 'children'),
        Output('query-output', component_property='style'),
        Output('loading', 'children'),
        [Input('run-query-button', 'n_clicks')],
        [dash.dependencies.State('query-input', 'value')]
    )
    @requires_auth
    def update_output(n_clicks, query):
        bqclient = bigquery.Client()
        print('query: ', query)
        if n_clicks == 0:
            raise PreventUpdate

        
        df = pd.read_gbq(query, bqclient)
        print(df)
        # Display the query result
        return ([dash_table.DataTable(data=df.to_dict('records'),
                                        id='query-table'),
                    html.Br(),
                    dcc.Input(id='downl-table-name', type='text', 
                            placeholder='Enter table name'),
                    html.Button('downl table',
                                id='downl-table-btn',
                                className='btn btn-block btn-primary mb-3',
                                disabled=True)], 
                {'display': 'block'},
                True)


