import re
import hashlib

from dash import html, Dash, dcc
import dash_bootstrap_components as dbc

def create_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def add_copy_button_to_code_blocks(text):
    # Find all code blocks
    blocks = text.split("```")
    print(blocks)

    # Initialize an empty list to hold the processed blocks
    processed_blocks = []

    # Iterate over the blocks
    for i, block in enumerate(blocks):
        # If the block is a code block, add a copy button
        if i % 3 == 1:  # Code blocks are at odd indices because of the way we split the text
            clipid = create_hash(block)
            mdblock = "```\n" + block + "\n```"
            processed_blocks.extend([dcc.Markdown(mdblock, id=clipid),
                                     dcc.Clipboard(target_id=clipid,
                                                   style={"position": "absolute",
                                                          "top": 0,
                                                          "right": 20,
                                                          "fontSize": 20})
                                    ])
        else:
            processed_blocks.append(dcc.Markdown(block))
    return processed_blocks


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
        textbox_human = dbc.Card(dcc.Markdown(text), style=style, body=True,
                                 color="primary", inverse=True)
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

        textbox = dbc.Card(dcc.Markdown(text), style=style, body=True, 
                           color="light-blue", inverse=False)

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
        text_with_copy_buttons = add_copy_button_to_code_blocks(text)
        textbox = dbc.Card(children=text_with_copy_buttons,
                           style=style, body=True,
                           color="light", inverse=False)

        return html.Div([thumbnail_AI, textbox])


    else:

        raise ValueError("Incorrect option for `box`.")