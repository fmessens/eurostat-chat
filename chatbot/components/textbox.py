from dash import html, Dash, dcc
import dash_bootstrap_components as dbc


def render_textbox(text:str, app:Dash, box:str = "AI"):
    text = text.replace(f"AI:", "").replace("Human:", "").replace("Prompt:", "")
    text = text.replace('\n', '  \n')
    style = {
        "max-width": "60%",
        "width": "max-content",
        "padding": "5px 10px",
        "border-radius": 25,
        "margin-bottom": 20,
        'border': '0px solid'
    }

    if box == "Human":
        style["margin-left"] = "auto"
        style["margin-right"] = 50

        thumbnail_human = html.Img(
            src=app.get_asset_url("img/smile-emoticon.png"),
            style={
                "border-radius": 50,
                "height": 36,
                "margin-left": 5,
                "float": "right",
            },
        )
        textbox_human = dbc.Card(dcc.Markdown(text), style=style, body=True, color="primary", inverse=True)
        return html.Div([thumbnail_human, textbox_human])
    
    elif box == "Prompt":
        style["margin-left"] = "auto"
        style["margin-right"] = 50

        thumbnail_prompt = html.Img(
            src=app.get_asset_url("img/mechanical.png"),
            style={
                "border-radius": 50,
                "height": 36,
                "margin-left": 5,
                "float": "right",
            },
        )
        textbox = dbc.Card(dcc.Markdown(text), style=style, body=True, color="light-blue", inverse=False)

        return html.Div([thumbnail_prompt, textbox])

    elif box == "AI":
        style["margin-left"] = 50
        style["margin-right"] = "auto"

        thumbnail_AI = html.Img(
            src=app.get_asset_url("img/robot.png"),
            style={
                "border-radius": 50,
                "height": 36,
                "margin-right": 5,
                "float": "left",
            },
        )
        textbox = dbc.Card(dcc.Markdown(text), style=style, body=True, color="light", inverse=False)

        return html.Div([thumbnail_AI, textbox])


    else:

        raise ValueError("Incorrect option for `box`.")