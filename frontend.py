import json
import threading
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import os
from flask import send_from_directory

from voting_aid_methods import get_topics_and_descriptions, get_parties_context_of_political_positions

app = dash.Dash(__name__)

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

app.layout = html.Div([
    html.H1("VotingAid", style={'text-align': 'center', 'font-family': 'Arial, sans-serif', 'color': '#880033'}),
    html.Div([
        html.P([
            html.Strong("VotingAid"),
            " ist ein Tool, das Ihnen dabei hilft, Ihre politische Position mit den Positionen verschiedener Parteien "
            "zu vergleichen. Derzeit basiert das Tool ausschließlich auf den Parteiprogrammen der jeweiligen Parteien.",
            html.Br(),
            "Geben Sie Ihre politischen Meinungen in die Textbox unten ein, z. B. 'Klimaschutz ist wichtig' oder "
            "'Die Wirtschaft soll liberalisiert werden'. Je präziser Ihre Angaben sind, desto genauer ist das "
            "Endergebnis. Wenn Sie fertig sind, können Sie auf den Button ",
            html.Strong("Zusammenfassen"),
            " klicken. Ihre Eingaben werden dann in verschiedene Themengebiete unterteilt, die Sie bei Bedarf noch "
            "einmal bearbeiten können. 'Thema' steht dabei für eine Kategorie, wie z. B. Klimaschutz, und 'Ansicht' "
            "für Ihre spezifischen Meinungen und Lösungsvorschläge zu diesem Thema. Um das Ergebnis zu sehen, klicken "
            "Sie auf den Button ",
            html.Strong("Analysiere"),
            ". Sie erhalten anschließend eine Übersicht über die Parteien und deren Positionen zu den Themen. ",
            "Bitte beachten Sie, dass die Analyse einige Zeit in Anspruch nehmen kann."
        ], style={'text-align': 'center'}),
        html.P([
            html.Strong("Es werden keine Daten innerhalb dieses Tools gespeichert!", style = {'color': '#880033'})
        ], style={'text-align': 'center'}),
        html.P([
            html.Strong("Hinweis:", style={'color': '#880033'}),
            " Die Analyse kann etwas Zeit in Anspruch nehmen, insbesondere wenn Sie viele Themen eingeben."
        ], style={'text-align': 'center'}),
        html.P([
            html.Em("Bitte beachten Sie, dass sich das Tool noch in der Entwicklungsphase befindet.")
        ], style={'text-align': 'center'}),

    ], style={'font-family': 'Arial, sans-serif', 'margin-left': '20px', 'margin-right': '20px'}),
    dcc.Textarea(
        id='political-position-input',
        placeholder='Beispiel: Klimaschutz ist mir wichtig. Ich finde, dass erneuerbare Energien stärker gefördert '
                    'werden sollten und der Ausstieg aus fossilen Brennstoffen beschleunigt werden muss. Gleichzeitig '
                    'halte ich es für essenziell, die wirtschaftliche Stabilität zu gewährleisten.',
        style={'width': '95%', 'height': 200, 'padding': '10px', 'font-family': 'Arial, sans-serif',
               'border': '1px solid #ccc', 'border-radius': '5px'}
    ),
    html.Div([
        html.Button('Zusammenfassen', id='analyze-button', n_clicks=0,
                    style={'margin': '10px', 'padding': '10px 20px', 'font-family': 'Arial, sans-serif',
                           'background-color': '#880033', 'color': '#fff', 'border': 'none', 'border-radius': '5px',
                           'cursor': 'pointer'})
    ], style={'text-align': 'center'}),
    html.Div(id='topics-positions-container', style={'margin-top': '20px'}),
    dcc.Loading(
        id="loading",
        type="default",
        style={'color': '#880033'},
        children=html.Div(id='final-score-output', style={'margin-top': '20px'})
    )
])

@app.callback(
    Output('topics-positions-container', 'children'),
    Input('analyze-button', 'n_clicks'),
    State('political-position-input', 'value')
)
def analyze_political_position(n_clicks, political_position):
    if n_clicks == 0:
        return []

    topics, positions = get_topics_and_descriptions(political_position)

    topics_positions_inputs = [
        html.Div([
            html.Div([
                dcc.Markdown("**Thema:**", style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}),
                dcc.Textarea(
                    id={'type': 'topic-input', 'index': i},
                    value=topic,
                    style={'width': '95%', 'height': 50, 'padding': '10px', 'font-family': 'Arial, sans-serif',
                           'border': '1px solid #ccc', 'border-radius': '5px'}
                ),
                dcc.Markdown("**Ansicht:**", style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}),
                dcc.Textarea(
                    id={'type': 'position-input', 'index': i},
                    value=position,
                    style={'width': '95%', 'height': 100, 'padding': '10px', 'font-family': 'Arial, sans-serif',
                           'border': '1px solid #ccc', 'border-radius': '5px'}
                )
            ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin-bottom': '10px', 'border-radius': '5px',
                      'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
            for i, (topic, position) in enumerate(zip(topics, positions))
        ]),
        html.Div([
            html.P("Klicken Sie auf 'Analysiere' um die LLM analyse zu starten. "
                   "Die Analyse kann einige Zeit in Anspruch nehmen.",
                   style={'font-family': 'Arial, sans-serif', 'margin-left': '20px', 'margin-right': '20px'}),
            html.Button('Erweitere um eine Thema-Ansicht Box', id='add-topic-position-button', n_clicks=0,
                        style={'margin': '10px', 'padding': '10px 20px', 'font-family': 'Arial, sans-serif',
                               'background-color': '#163c00', 'color': '#fff', 'border': 'none', 'border-radius': '5px',
                               'cursor': 'pointer', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            html.Button('Analysiere', id='submit-button', n_clicks=0,
                        style={'margin': '10px', 'padding': '10px 20px', 'font-family': 'Arial, sans-serif',
                               'background-color': '#880033', 'color': '#fff', 'border': 'none', 'border-radius': '5px',
                               'cursor': 'pointer', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'text-align': 'center'})
    ]

    return topics_positions_inputs

@app.callback(
    Output('topics-positions-container', 'children', allow_duplicate=True),
    Input('add-topic-position-button', 'n_clicks'),
    State('topics-positions-container', 'children'),
    prevent_initial_call=True
)
def add_topic_position(n_clicks, children):
    if n_clicks == 0:
        return children

    new_div = html.Div([
        dcc.Markdown("**Thema:**", style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}),
        dcc.Textarea(
            id={'type': 'topic-input', 'index': n_clicks},
            value='',
            style={'width': '95%', 'height': 50, 'padding': '10px', 'font-family': 'Arial, sans-serif',
                   'border': '1px solid #ccc', 'border-radius': '5px'}
        ),
        dcc.Markdown("**Ansicht:**", style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}),
        dcc.Textarea(
            id={'type': 'position-input', 'index': n_clicks},
            value='',
            style={'width': '95%', 'height': 100, 'padding': '10px', 'font-family': 'Arial, sans-serif',
                   'border': '1px solid #ccc', 'border-radius': '5px'}
        )
    ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin-bottom': '10px', 'border-radius': '5px',
              'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
    children.insert(-1, new_div)
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
                html.H3(party_names[party], style={'display': 'inline-block', 'font-family': 'Arial, sans-serif'}),
                html.H3("-\t" if scores['total'] == -1
                        else f"{scores['total']:.2f}%\t" if scores['total'] % 1 != 0 else f"{int(scores['total'])}%\t",
                    style={'display': 'inline-block', 'float': 'right', 'font-family': 'Arial, sans-serif',
                           'margin-right': '10px'}
                )
            ]),
            html.Div([
                html.Div([
                    html.Div([
                        html.H4(f"Thema: {topic}", style={'font-family': 'Arial, sans-serif', 'display': 'inline-block'}),
                        html.H4("Keine Position im Parteiprogramm",
                               style={'font-family': 'Arial, sans-serif', 'float': 'right','margin-right': '10px'})
                        if details['rating'] == -1 else
                        html.H4(f"{details['rating']:.2f}%" if details['rating'] % 1 != 0 else f"{int(details['rating'])}%",
                                style={'font-family': 'Arial, sans-serif', 'float': 'right', 'margin-right': '10px'}),
                    ]),
                    html.P(details['detailed_answer'], style={'font-family': 'Arial, sans-serif'}),
                    html.Div([
                        html.A(f"[{details['metadata'][i]['title']}]", id={'type': 'source-button', 'index': i},
                               href=f"/local-files/{details['metadata'][i]['url']}",
                               style={'margin-right': '10px', 'font-family': 'Arial, sans-serif'})
                        for i, metadata in enumerate(details['metadata'])
                    ], style={'margin-top': '10px'})
                ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin-bottom': '10px',
                          'border-radius': '5px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
                for topic, details in scores.items() if topic != 'total'
            ])
        ], style={'border': f'2px solid {party_colors[party]}', 'padding': '10px', 'margin-bottom': '10px',
                  'border-radius': '5px', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
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