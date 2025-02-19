import json
import threading
from pydoc import classname

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH
import os
from flask import send_from_directory

from util import pop_random_entry
from voting_aid_methods import get_parties_context_of_political_positions

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

potential_topics_and_positions = {
    "Unterstützung der Ukraine": "Die Ukraine soll...",
    "Erneuerbare Energien": "Erneuerbare Energien sollen...",
    "Bürgergeld": "Das Bürgergeld soll...",
    "Tempolimit auf Autobahnen": "Ein Tempolimit auf Autobahnen soll...",
    "Asyl": "Asylsuchende sollen...",
    "Mietpreisbremse": "Die Mietpreisbremse soll...",
    "Videoüberwachung": "Die Videoüberwachung an öffentlichen Orten soll...",
    "Rente": "Die Rente soll...",
    "Fachkräfte aus dem Ausland": "Fachkräfte...",
    "Atomkraft": "Die Atomkraft soll...",
    "Bund und Bildung": "Der Bund soll in der Bildung...",
    "Rüstungsexporte in Krisengebiete": "Rüstungsexporte sollen...",
    "Frauenquote": "Die Frauenquote soll...",
    "Ökologische Landwirtschaft": "Die Landwirtschaft soll...",
    "AfD Verbot": "Die AfD soll...",
    "Lieferkettenschutzgesetz": "Das Lieferkettenschutzgesetz soll...",
    "BAföG": "Das BAföG soll...",
    "Schuldenbremse": "Die Schuldenbremse soll...",
    "Klimaziele": "Die Klimaziele sollen...",
    "Kohleausstieg": "Der Kohleausstieg soll...",
    "Schwangerschaftsabbruch": "Der Schwangerschaftsabbruch soll...",
    "Euro": "Der Euro soll...",
    "Verkehrswende": "Die Verkehrswende soll...",
    "Volksentscheide": "Volksentscheide sollen...",
    "Strafrecht für unter 14-Jährige": "Das Strafrecht für ...",
    "Zölle": "Zölle sollen...",
    "Zweite Staatsbürgerschaft": "Die zweite Staatsbürgerschaft soll...",
    "Heizungen": "Heizungen sollen...",
    "Mindestlohn": "Der Mindestlohn soll...",
    "Verteidigungsausgaben": "Die Verteidigungsausgaben sollen...",
    "Entwicklungszusammenarbeit": "Die Entwicklungszusammenarbeit soll...",
    "Großspenden an Parteien": "Großspenden an Parteien sollen...",
    "Verbrennungsmotoren": "Verbrennungsmotoren sollen...",
    "Vermögenssteuer": "Die Vermögenssteuer soll...",
    "Unternehmenssteuern": "Die Unternehmenssteuern sollen...",
    "Einkommenssteuer": "Die Einkommenssteuer soll...",
    "Mehrwertsteuer": "Die Mehrwertsteuer soll...",
    "Rundfunkbeitrag": "Der Rundfunkbeitrag soll...",
    "Cannabis": "Cannabis soll...",
    "Doppelte Staatsbürgerschaft": "Die doppelte Staatsbürgerschaft soll...",
    "CO2-Preis": "Der CO2-Preis soll...",
    "Digitalisierung": "Die Digitalisierung soll...",
    "KI": "Der Einsatz von Künstlicher Intelligenz soll...",
    "Gesundheit & Pflege": "Das Gesundheitssystem...",
    "Innere Sicherheit": "Die innere Sicherheit...",
    "Cyberkriminalität": "Cyberkriminalität...",
    "Infrastruktur & Verkehr": "Die Verkehrsinfrastruktur...",
    "Europäische Union": "Die Europäische Union...",
}

topic_position_create_index = 0
def get_topic_position_box():
    global topic_position_create_index
    topic_position_create_index += 1
    return \
        html.Div([
            html.Div([
                html.Div([
                    dcc.Markdown("**Thema:**"),
                    html.Button('Thema Vorschlagen',
                                id={'type': 'suggest-topic-button', 'index': topic_position_create_index},
                                className='suggest-topic-button')
                ], style={'display': 'flex', 'justify-content': 'space-between'}),
                dcc.Textarea(
                    id={'type': 'topic-input', 'index': topic_position_create_index},
                    value="",
                    style={'height': '20px'}
                )
            ]),
            html.Div([
                dcc.Markdown("**Ansicht:**", style={'display': 'flex'}),
                dcc.Textarea(
                    id={'type': 'position-input', 'index': topic_position_create_index},
                    value="",
                    style={'height': '100px'}
                )
            ])
        ], className='topic-position-box')


app.layout = html.Div([
    html.H1("VotingAid"),
    html.Div([
        html.P([
            html.Strong("VotingAid"),
            " ist ein Tool, das Ihnen dabei hilft, Ihre politische Position mit den Positionen verschiedener Parteien "
            "zu vergleichen. Derzeit basiert das Tool ausschließlich auf den Parteiprogrammen der jeweiligen Parteien.",
            html.Br(),
            "Geben Sie Ihre politischen Meinungen in die Thema-Box unten ein. 'Thema' steht dabei für eine "
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
        get_topic_position_box(),
        html.Div([
            html.Em("Klicken Sie auf 'Analysiere' um die LLM analyse zu starten. "
                   "Die Analyse kann einige Zeit in Anspruch nehmen."),
            html.Br(),
            html.Button('Erweitere die Analyse um ein Thema', id='add-topic-position-button', n_clicks=0),
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
    Output({'type': 'topic-input', 'index': MATCH}, 'value'),
    Output({'type': 'position-input', 'index': MATCH}, 'value'),
    Input({'type': 'suggest-topic-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'topic-input', 'index': MATCH}, 'value'),
    State({'type': 'position-input', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def suggest_topic(n_clicks, current_topic, current_position):
    if n_clicks > 0:
        suggested_topic, suggested_position = pop_random_entry(potential_topics_and_positions)
        return suggested_topic, suggested_position
    return current_topic, current_position

@app.callback(
    Output('topics-positions-container', 'children', allow_duplicate=True),
    Input('add-topic-position-button', 'n_clicks'),
    State('topics-positions-container', 'children'),
    prevent_initial_call=True
)
def add_topic_position(n_clicks, children):
    if n_clicks == 0:
        return children

    children.insert(-1, get_topic_position_box())
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
                    dcc.Markdown(details['detailed_answer'], style={'text-align': 'left', 'display': 'inline-block'}),
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