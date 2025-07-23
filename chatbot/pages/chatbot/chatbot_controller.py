import time
import json

from dash.dependencies import Input, Output, State
import dash
from langchain_core.messages import HumanMessage, AIMessage

from chatbot.components.textbox import render_textbox
from chatbot.pages.chatbot.chatbot_promptflow import (first_prompt, 
                                                      chat,
                                                      second_prompt,
                                                      third_prompt,
                                                      fourth_prompt)
from chatbot.pages.chatbot.chatbot_ragflow import rag_chain

def conditional_textbox(intxt, app):
    firstm = intxt.split(':')[0]
    if firstm=='AI':
        return render_textbox(intxt, app=app, box="AI")
    elif firstm=='Prompt':
        return render_textbox(intxt, app=app, box="Prompt")
    else:
        return render_textbox(intxt, app=app, box="Human")
    

def prep_bot_content(inls):
    outls = []
    for msg in inls:
        if msg.type in ('human', 'system'):
            outls.append(f'<split>Prompt: {msg.content}')
        elif msg.type=='ai':
            outls.append(f'<split>AI: {msg.content}')
        else:
            raise ValueError('Message type not recognized')
    outstr = ''.join(outls)
    return [outstr]




def init_callbacks(app):
    @app.callback(
        Output(component_id="display-conversation", component_property="children"), 
        Input(component_id="store-bot-conversation", component_property="data"),
        Input(component_id="store-human-conversation", component_property="data")
    )
    def update_display(bot_q, human_q):
        bot_qp = json.loads(bot_q)
        human_qp = json.loads(human_q)
        chat_history = ''
        for hq in human_qp:
            chat_history += f'<split>Human: {hq}'
            if len(bot_qp) > 0:
                chat_history += bot_qp.pop(0)
        return [
            conditional_textbox(x, app)
            for x in chat_history.split("<split>")[1:]
        ]


    @app.callback(
        Output(component_id="user-input", component_property="value"),
        Input(component_id="submit", component_property="n_clicks"), 
        Input(component_id="user-input", component_property="n_submit"),
    )
    def clear_input(n_clicks, n_submit):
        return ""
    
    @app.long_callback(
        output=[Output(component_id="loading-component", 
                       component_property="children")],
        inputs=[Input(component_id="store-human-conversation", 
                      component_property="data")],
        state=[State(component_id="store-bot-conversation",
                     component_property="data"),
               State(component_id="prompt-chain",
                     component_property="value")],
        progress=Output(component_id="store-bot-conversation", 
                        component_property="data"), 
        running=[
            (Output("submit", "disabled"), True, False),
        ],
        prevent_initial_call=True,
    )
    def run_chatbot(set_progress, human_q, bot_q, checkv):
        ctx = dash.callback_context
        if not ctx.triggered[0]["prop_id"]=="store-human-conversation.data":
            return [False]
        bot_qp = json.loads(bot_q)
        human_qp = json.loads(human_q)
        last_humanq = human_qp[-1]
        if checkv==[' Activate prompt chain (no chat history)']:
            messages = first_prompt(last_humanq)
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            messages += [chat.invoke(messages)]
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            messages += second_prompt(messages[-1].content, last_humanq)
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            messages += [chat.invoke(messages)]
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            outprompt, cols = third_prompt(messages[-1].content, last_humanq)
            messages += outprompt
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            messages += [chat.invoke(messages)]
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))
            """
            messages += fourth_prompt(messages[-1].content, last_humanq)
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))

            messages += [chat.invoke(messages)]
            set_progress(json.dumps(bot_qp + prep_bot_content(messages)))
            """
            time.sleep(10)
        else:
            chat_history = []
            for h,b in zip(human_qp[:-1], bot_qp):
                chat_history.append(HumanMessage(content=h))
                for bs in b.split('<split>'):
                    if bs:
                        chat_history.append(AIMessage(content=bs))
            ai_msg = rag_chain.invoke({"question": last_humanq, 
                                       "chat_history": chat_history})
            set_progress(json.dumps(bot_qp + prep_bot_content([ai_msg])))
            time.sleep(10)
        return [False]
    

    @app.callback(
        Output(component_id="store-human-conversation", component_property="data"),
        Input(component_id="submit", component_property="n_clicks"),
        State(component_id="user-input", component_property="value"),
        State(component_id="store-human-conversation", component_property="data"),
        prevent_initial_call=True,
    )
    def update_human_conversation(n_clicks, user_input, data):
        datap = json.loads(data)
        ctx = dash.callback_context
        if not ctx.triggered[0]["prop_id"]=="submit.n_clicks":
            return json.dumps(datap)
        return json.dumps(datap + [user_input])