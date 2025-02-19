import json
import threading
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import os
from flask import send_from_directory

from voting_aid_methods import get_topics_and_descriptions, get_parties_context_of_political_positions

app = dash.Dash(__name__, external_stylesheets=['/assets/custom.css'])

party_colors = {
    "afd": "#009EE0",
    "bsw": "#4B0082",
    "fdp": "#FFED00",
    "gruene": "#64A12D",
    "linke": "#BE3075",
    "spd": "#E3000F",
    "union": "#000000"
}

party_names = {
    "afd": "Alternative für Deutschland (AfD)",
    "bsw": "Bündnis Sara Wagenknecht (BSW)",
    "fdp": "Freie Demokratische Partei (FDP)",
    "gruene": "Bündnis 90/Die Grünen",
    "linke": "Die Linke",
    "spd": "Sozialdemokratische Partei Deutschlands (SPD)",
    "union": "Christlich Demokratische Union Deutschlands/Christlich-Soziale Union in Bayern (CDU/CSU)"
}

topic_position_box = \
html.Div([
    html.Div([
        dcc.Markdown("**Thema:**", className='inline-block'),
        dcc.Textarea(
            id={'type': 'topic-input', 'index': 0},
            value="",
            className='inline-block',
            style={'height': '20px'}
        )
    ], className='text-align-left'),
    html.Div([
        dcc.Markdown("**Ansicht:**", className='inline-block'),
        dcc.Textarea(
            id={'type': 'position-input', 'index': 0},
            value="",
            className='inline-block',
            style={'height': '100px'}
        )
    ], className='text-align-left')
], className='topic-position-box')

app.layout = html.Div([
    html.H1("VotingAid"),
    html.Div([
        html.P([
            html.Strong("VotingAid"),
            " ist ein Tool, das Ihnen dabei hilft, Ihre politische Position mit den Positionen verschiedener Parteien "
            "zu vergleichen. Derzeit basiert das Tool ausschließlich auf den Parteiprogrammen der jeweiligen Parteien.",
            html.Br(),
            "Geben Sie Ihre politischen Meinungen in die Thema-Ansicht Box unten ein. 'Thema' steht dabei für eine "
            "Kategorie, wie z. B. Klimaschutz, und 'Ansicht' für Ihre spezifischen Meinungen und Lösungsvorschläge "
            "zu diesem Thema. Je präziser Ihre Angaben sind, desto genauer ist das Endergebnis. "
            "Bitte teilen Sie ihre Meinungen in unterschiedliche Themengebiete auf."
            "Um das Ergebnis zu sehen, klicken Sie auf den Button ",
            html.Strong("Analysiere"),
            ". Im Anschluss erhalten Sie einen Überblick über die Parteien und ihre Positionen zu den einzelnen "
            "Themen, basierend auf den jeweiligen Parteiprogrammen.",
            "Bitte beachten Sie, dass die Analyse einige Zeit in Anspruch nehmen kann."
        ]),
        html.P([
            html.Strong("Es werden keine Daten innerhalb dieses Tools gespeichert!")
        ]),
        html.P([
            html.Strong("Hinweis:"),
            " Die Analyse kann etwas Zeit in Anspruch nehmen, insbesondere wenn Sie viele Themen eingeben."
        ]),
        html.P([
            html.Em("Bitte beachten Sie, dass sich das Tool noch in der Entwicklungsphase befindet.")
        ]),

    ]),
    html.Div([
        topic_position_box,
        html.Div([
            html.P("Klicken Sie auf 'Analysiere' um die LLM analyse zu starten. "
                   "Die Analyse kann einige Zeit in Anspruch nehmen."),
            html.Button('Erweitere um eine Thema-Ansicht Box', id='add-topic-position-button', n_clicks=0),
            html.Button('Analysiere', id='submit-button', n_clicks=0)
        ], style={'text-align': 'center'})
    ], id='topics-positions-container', style={'margin-top': '20px'}),

    dcc.Loading(
        id="loading",
        type="default",
        style={'color': '#880033'},
        children=html.Div(id='final-score-output', style={'margin-top': '20px'})
    )
])

@app.callback(
    Output('topics-positions-container', 'children', allow_duplicate=True),
    Input('add-topic-position-button', 'n_clicks'),
    State('topics-positions-container', 'children'),
    prevent_initial_call=True
)
def add_topic_position(n_clicks, children):
    if n_clicks == 0:
        return children

    children.insert(-1, topic_position_box)
    return children

def perform_analysis(parties, topics, positions, max_answer_length, output):
    final_score = get_parties_context_of_political_positions(parties, topics, positions, max_answer_length)
    output.append(final_score)

@app.callback(
    Output('final-score-output', 'children'),
    Input('submit-button', 'n_clicks'),
    State({'type': 'topic-input', 'index': dash.dependencies.ALL}, 'value'),
    State({'type': 'position-input', 'index': dash.dependencies.ALL}, 'value')
)
def submit_analysis(n_clicks, topics, positions):
    if n_clicks == 0:
        return ""

    parties = ["spd", "union", "gruene", "fdp", "afd", "linke", "bsw"]
    max_answer_length = 600
    output = []

    analysis_thread = threading.Thread(target=perform_analysis,
                                       args=(parties, topics, positions, max_answer_length, output))
    analysis_thread.start()
    analysis_thread.join()

    final_score = output[0]

    final_score = dict(sorted(final_score.items(), key=lambda item: item[1]['total'], reverse=True))
    party_boxes = []
    for party, scores in final_score.items():
        party_box = html.Div([
            html.Div([
                html.H3(party_names[party]),
                html.H3("-\t" if scores['total'] == -1
                        else f"{scores['total']:.2f}%\t" if scores['total'] % 1 != 0 else f"{int(scores['total'])}%\t",
                    className='float-right'
                )
            ]),
            html.Div([
                html.Div([
                    html.Div([
                        html.H4(f"Thema: {topic}"),
                        html.H4("Keine Position im Parteiprogramm", className='float-right')
                        if details['rating'] == -1 else
                        html.H4(f"{details['rating']:.2f}%" if details['rating'] % 1 != 0 else f"{int(details['rating'])}%",
                                className='float-right'),
                    ]),
                    html.P(details['detailed_answer']),
                    html.Div([
                        html.A(f"[{details['metadata'][i]['title']}]", id={'type': 'source-button', 'index': i},
                               href=f"/local-files/{details['metadata'][i]['url']}")
                        for i, metadata in enumerate(details['metadata'])
                    ], style={'margin-top': '10px'})
                ], className='party-box')
                for topic, details in scores.items() if topic != 'total'
            ])
        ], className='party-box', style={'border': f'2px solid {party_colors[party]}'})
        party_boxes.append(party_box)

    return party_boxes


@app.server.route('/local-files/<path:filename>')
def serve_local_file(filename):
    return send_from_directory(os.getcwd(), filename)


if __name__ == '__main__':
    try:
        app.run_server(debug=True)
    except OSError as e:
        print(f"An error occurred: {e}")