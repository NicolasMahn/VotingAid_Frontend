import json
import threading
from pydoc import classname

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
import os
from flask import send_from_directory

import voting_aid_methods
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


def get_party_box(party, scores):
    return html.Div([
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
                    html.Div(
                        dcc.Markdown(details['detailed_answer'],
                                     style={'text-align': 'left', 'display': 'flex-block'}),
                    id={'type': 'position-output', 'index': f'{topic}_{party}'},),
                    html.Div([
                        html.A(f"[{details['metadata'][i]['title']}]", id={'type': 'source-button', 'index': i},
                               href=f"/local-files/{details['metadata'][i]['url']}")
                        for i, metadata in enumerate(details['metadata'])
                    ], style={'margin-top': '10px'}),
                    html.Button('Nochmal analysieren', id={'type': 'recalculate-button', 'index': f'{topic}_{party}'},
                                className='recalculate-button'),
                ], className='party-box')
                for topic, details in scores.items() if topic != 'total'
            ])
        ], className='party-box', style={'border': f'2px solid {party_colors[party]}'})

global saved_final_score
saved_final_score = None

def get_party_boxes(final_score):
    party_boxes = []
    for party, scores in final_score.items():
        party_boxes.append(get_party_box(party, scores))
    return party_boxes

loading_animation = html.Div(className='spinner-container', children=[
        html.Div(className='spinner')
    ])

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
        ]),
        html.P([
            html.Strong("Es werden keine Daten innerhalb dieses Tools gespeichert!")
        ]),
        html.P([
            html.Em("Bitte beachten Sie, dass das Tool noch ein Prototyp ist.")
        ]),

    ]),
    html.Div([
        get_topic_position_box(),
    ], id='topics-positions-container', style={'margin-top': '20px'}),
    html.Div([
        html.Em("Klicken Sie auf 'Analysiere' um die LLM analyse zu starten. "
                "Die Analyse kann einige Zeit in Anspruch nehmen."),
        html.Br(),
        html.Button('Erweitere die Analyse um ein Thema', id='add-topic-position-button', n_clicks=0),
        html.Button('Analysiere', id='submit-button', n_clicks=0)
    ], style={'text-align': 'center'}),
    html.Div(id='final-score-output', style={'margin-top': '20px'}),
    dcc.Interval(
        id='interval-component',
        interval= 1000,
        n_intervals=0
    ),
    dcc.Store(id='final-score-store')
])

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>VotingAid</title>
        <link rel="stylesheet" href="/assets/custom.css">
        {%metas%}
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            <p class="impressum">
                <b>Impressum:</b>
                Nicolas Mahn; Untere Brandstraße 62 70567 Stuttgart, Deutschland;
                Telefon: +49 (0) 152 06501315; E-Mail: nicolas.mahn@gmx.de
            </p>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

@app.callback(
    Output('final-score-store', 'data', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    State('final-score-store', 'data'),
    prevent_initial_call=True
)
def check_final_score(n_intervals, stored_final_score):
    global saved_final_score
    if stored_final_score != saved_final_score:
        print("storing final score: ", saved_final_score, "\n", stored_final_score)
        return saved_final_score
    return dash.no_update


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
    Output('topics-positions-container', 'children'),
    Input('add-topic-position-button', 'n_clicks'),
    State('topics-positions-container', 'children')
)
def add_topic_position(n_clicks, children):
    if n_clicks == 0:
        return children

    children.append(get_topic_position_box())
    return children

def perform_analysis(parties, topics, positions, max_answer_length, output):
    final_score = get_parties_context_of_political_positions(parties, topics, positions, max_answer_length)
    output.append(final_score)

@app.callback(
    Output('final-score-output', 'children', allow_duplicate=True),
    Input('submit-button', 'n_clicks'),
    State({'type': 'topic-input', 'index': ALL}, 'value'),
    State({'type': 'position-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def submit_analysis(n_clicks, topics, positions):
    if n_clicks == 0:
        pass

    threading.Thread(target=run_analysis, args=(topics, positions)).start()

    return loading_animation

def run_analysis(topics, positions):
    parties = ["spd", "union", "gruene", "fdp", "afd", "linke", "bsw"]
    max_answer_length = 600
    output = []

    analysis_thread = threading.Thread(target=perform_analysis,
                                       args=(parties, topics, positions, max_answer_length, output))
    analysis_thread.start()
    analysis_thread.join()

    final_score = output[0]

    # final_score = {'spd': {'Bund und Bildung': {'detailed_answer': 'Deine Meinung, dass der Bund in der Bildung Verantwortung übernehmen sollte, stimmt eng mit der Position der SPD überein. Die SPD betont, dass gute Bildung für alle unabdingbar ist und fordert eine starke, gesamtstaatliche Finanzierung, um Chancengleichheit in der Bildung zu gewährleisten. Sie steht für eine enge Zusammenarbeit zwischen Bund, Ländern und Gemeinden, um Bildungsqualität und Betreuung zu verbessern. Dies reflektiert ein Verständnis für die Notwendigkeit einer aktiven Rolle des Bundes in der Bildungslandschaft. Nur einige kleinere Differenzen in spezifischen Maßnahmen könnten die 100% schmälern.', 'rating': 90, 'metadata': [{'id': 'SPD_Programm_bf.pdf_Wir kämpfen dafür, dass gute Bildung für alle zuverlässig gelingt._0', 'page': 15, 'pdf_name': 'SPD_Programm_bf.pdf', 'title': 'Wir kämpfen dafür, dass gute Bildung für alle zuverlässig gelingt.', 'url': 'data/spd/SPD_Programm_bf.pdf#page=15'}, {'id': 'SPD_Programm_bf.pdf_Worauf es jetzt ankommt_0', 'page': 4, 'pdf_name': 'SPD_Programm_bf.pdf', 'title': 'Worauf es jetzt ankommt', 'url': 'data/spd/SPD_Programm_bf.pdf#page=4'}, {'id': 'SPD_Programm_bf.pdf_Ein neuer Aufschwung für Deutschland_0', 'page': 6, 'pdf_name': 'SPD_Programm_bf.pdf', 'title': 'Ein neuer Aufschwung für Deutschland', 'url': 'data/spd/SPD_Programm_bf.pdf#page=6'}]}, 'total': 90.0}, 'union': {'Bund und Bildung': {'detailed_answer': 'Ihre Position, dass der Bund in der Bildung eine Rolle spielen soll, wird von der Partei teilweise geteilt. Sie betont die Notwendigkeit einer verbesserten Zusammenarbeit zwischen Bund und Ländern, ohne die Zuständigkeiten in Frage zu stellen. Die Partei sieht den Bund als Unterstützer in der Bildungsförderung, besonders in Bezug auf Chancengleichheit und Innovation. Dennoch bleibt der Fokus auf den Ländern, was bedeutet, dass die Rolle des Bundes wie beschrieben nicht zentralisiert ist. Ihre Meinung und die der Partei stimmen in der Ansprache an zentralen Themen überein, jedoch nicht in der Intensität der gewünschten Bundesverantwortung.', 'rating': 60, 'metadata': [{'id': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf_Ja zu Aufstieg durch Bildung_0', 'page': 64, 'pdf_name': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf', 'title': 'Ja zu Aufstieg durch Bildung', 'url': 'data/union/km_btw_2025_wahlprogramm_langfassung_ansicht.pdf#page=64'}, {'id': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf_Unser Plan für ein Land, das wieder zusammenhält_0', 'page': 56, 'pdf_name': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf', 'title': 'Unser Plan für ein Land, das wieder zusammenhält', 'url': 'data/union/km_btw_2025_wahlprogramm_langfassung_ansicht.pdf#page=56'}, {'id': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf_Ja zu leistungsstarker beruflicher und akademischer Bildung_0', 'page': 66, 'pdf_name': 'km_btw_2025_wahlprogramm_langfassung_ansicht.pdf', 'title': 'Ja zu leistungsstarker beruflicher und akademischer Bildung', 'url': 'data/union/km_btw_2025_wahlprogramm_langfassung_ansicht.pdf#page=66'}]}, 'total': 60.0}, 'gruene': {'Bund und Bildung': {'detailed_answer': 'Deine Position entspricht stark den Ansichten der Partei zur Rolle des Bundes in der Bildung, insbesondere in Bezug auf die Unterstützung für Chancengleichheit, Integration und Digitalisierung der Schulen. Die Partei befürwortet eine aktive Rolle des Bundes in der Finanzierungs- und Bildungsstruktur, was mit deiner Meinung übereinstimmt, dass der Bund Verantwortung übernehmen sollte. Die Betonung auf fachlicher Unterstützung und gemeinsamen Programmen zur Verbesserung der Bildungsbedingungen deutet auf eine harmonische Sichtweise hin. Insgesamt kann gesagt werden, dass die Position des Bundes als Förderer und Gestalter im Bildungsbereich von der Partei stark unterstützt wird.', 'rating': 80, 'metadata': [{'id': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf_Für starke Schulen für alle Kinder_0', 'page': 76, 'pdf_name': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf', 'title': 'Für starke Schulen für alle Kinder', 'url': 'data/gruene/20250205_Regierungsprogramm_DIGITAL_DINA5.pdf#page=76'}, {'id': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf_Für eine gute Berufsbildung, die allen offensteht_0', 'page': 78, 'pdf_name': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf', 'title': 'Für eine gute Berufsbildung, die allen offensteht', 'url': 'data/gruene/20250205_Regierungsprogramm_DIGITAL_DINA5.pdf#page=78'}, {'id': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf_Für einen Staat, der für die Menschen funktioniert_0', 'page': 32, 'pdf_name': '20250205_Regierungsprogramm_DIGITAL_DINA5.pdf', 'title': 'Für einen Staat, der für die Menschen funktioniert', 'url': 'data/gruene/20250205_Regierungsprogramm_DIGITAL_DINA5.pdf#page=32'}]}, 'total': 80.0}, 'fdp': {'Bund und Bildung': {'detailed_answer': 'Ihre Meinung, dass der Bund eine zentrale Rolle in der Bildung übernehmen sollte, spiegelt sich stark in der Position der Freien Demokraten wider. Die Partei fordert eine Reform des Bildungsföderalismus, die einheitliche Standards und eine stärkere Verantwortung des Bundes in der Bildung vorsieht. Außerdem befürworten sie die Schaffung von bundesweiten Qualitätsstandards und eine zentrale Finanzierung, was Ihre Vorstellung von einer aktiven Rolle des Bundes unterstützt. Daher liegt die Übereinstimmung Ihrer Auffassung mit der Partei bei 80%.', 'rating': 80, 'metadata': [{'id': 'fdp-wahlprogramm_2025.pdf_Moderne und selbstständige Schulen – bessere Bildungschancen für alle_0', 'page': 8, 'pdf_name': 'fdp-wahlprogramm_2025.pdf', 'title': 'Moderne und selbstständige Schulen – bessere Bildungschancen für alle', 'url': 'data/fdp/fdp-wahlprogramm_2025.pdf#page=8'}, {'id': 'fdp-wahlprogramm_2025.pdf_Weltbeste Bildung für selbstbewusste Bürger_0', 'page': 7, 'pdf_name': 'fdp-wahlprogramm_2025.pdf', 'title': 'Weltbeste Bildung für selbstbewusste Bürger', 'url': 'data/fdp/fdp-wahlprogramm_2025.pdf#page=7'}, {'id': 'fdp-wahlprogramm_2025.pdf_Große Chancen für die Kleinsten: Frühkindliche Bildung stärken_0', 'page': 7, 'pdf_name': 'fdp-wahlprogramm_2025.pdf', 'title': 'Große Chancen für die Kleinsten: Frühkindliche Bildung stärken', 'url': 'data/fdp/fdp-wahlprogramm_2025.pdf#page=7'}]}, 'total': 80.0}, 'afd': {'Bund und Bildung': {'detailed_answer': 'Basierend auf deiner politischen Meinung, dass der Bund in der Bildung eine zentrale Rolle übernehmen sollte, und der Position der AfD, die einen weniger zentralen Ansatz verfolgt und stattdessen eine Bildungspflicht anstelle von Schulpflicht fordert, scheint es eine geringe Übereinstimmung zu geben.\n\nDie AfD kritisiert die gegenwärtige Schulpflicht und betont individuelle Leistungsansprüche, was im Widerspruch zu der Idee steht, dass der Bund eine stärkere Verantwortung im Bildungsbereich übernehmen sollte. Daher würde ich die Übereinstimmung in diesem Fall mit einer Bewertung von 20 einordnen.', 'rating': -1, 'metadata': [{'id': 'AfD_Bundestagswahlprogramm2025_web.pdf_Schulpflicht zur Bildungspflicht umwandeln_0', 'page': 160, 'pdf_name': 'AfD_Bundestagswahlprogramm2025_web.pdf', 'title': 'Schulpflicht zur Bildungspflicht umwandeln', 'url': 'data/afd/AfD_Bundestagswahlprogramm2025_web.pdf#page=160'}, {'id': 'AfD_Bundestagswahlprogramm2025_web.pdf_Mut zur Leistung_0', 'page': 159, 'pdf_name': 'AfD_Bundestagswahlprogramm2025_web.pdf', 'title': 'Mut zur Leistung', 'url': 'data/afd/AfD_Bundestagswahlprogramm2025_web.pdf#page=159'}, {'id': 'AfD_Bundestagswahlprogramm2025_web.pdf_Migration und Bildung_0', 'page': 162, 'pdf_name': 'AfD_Bundestagswahlprogramm2025_web.pdf', 'title': 'Migration und Bildung', 'url': 'data/afd/AfD_Bundestagswahlprogramm2025_web.pdf#page=162'}]}, 'total': -1}, 'linke': {'Bund und Bildung': {'detailed_answer': 'Deine Position, dass der Bund eine zentrale Rolle in der Bildung spielen sollte, entspricht stark der Position der Partei, die fordert, dass der Bund die Verantwortung für das Bildungssystem übernehmen und das Kooperationsverbot zwischen Bund und Ländern aufheben soll. Die Partei betont die Notwendigkeit von Investitionen in Bildung und fordert ein Bildungsrahmengesetz, um bundesweite Standards zu schaffen, was deine Überzeugung unterstützt. Auch die Forderungen nach gleichen Bildungschancen und einer Aufhebung sozialer Ungleichheiten finden Resonanz. Der hohe Fokus auf gleichberechtigte Zugänge und umfassende staatliche Unterstützung zeigt eine starke Übereinstimmung.', 'rating': 90, 'metadata': [{'id': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf_Gute Bildung_0', 'page': 38, 'pdf_name': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf', 'title': 'Gute Bildung', 'url': 'data/linke/Wahlprogramm_Langfassung_Linke-BTW25_01.pdf#page=38'}, {'id': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf_Ausbilden, sonst wird umgelegt_0', 'page': 39, 'pdf_name': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf', 'title': 'Ausbilden, sonst wird umgelegt', 'url': 'data/linke/Wahlprogramm_Langfassung_Linke-BTW25_01.pdf#page=39'}, {'id': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf_Eine Schule für alle_0', 'page': 39, 'pdf_name': 'Wahlprogramm_Langfassung_Linke-BTW25_01.pdf', 'title': 'Eine Schule für alle', 'url': 'data/linke/Wahlprogramm_Langfassung_Linke-BTW25_01.pdf#page=39'}]}, 'total': 90.0}, 'bsw': {'Bund und Bildung': {'detailed_answer': 'Ihre politische Meinung zur Rolle des Bundes in der Bildung zeigt ein starkes Interesse an der Verbesserung der Bildungsbedingungen und Chancengleichheit für alle Kinder in Deutschland. Dies spiegelt sich in den Forderungen im Parteiprogramm wider, wie dem Aufheben des Kooperationsverbots zwischen Bund und Ländern und dem Ziel, bundesweit gleiche Bildungsstandards zu schaffen. Beide Positionen betonen die Notwendigkeit einer systematischen Förderung individueller Talente und der Überwindung sozialer Selektion im Bildungssystem. Zusätzlich wird die Dringlichkeit betont, Lehrer einzustellen und Bildungseinrichtungen zu finanzieren, was direkt mit Ihrem Anliegen zusammenhängt. Ihre Meinung und das Parteiprogramm zeigen eine hohe Übereinstimmung in der Ansicht, dass der Bund eine aktivere Rolle in der Bildungspolitik übernehmen sollte.', 'rating': 85, 'metadata': [{'id': 'BSW Wahlprogramm 2025.pdf_Beste Bildung für alle, von der Küste bis zu den Alpen!_1', 'page': 23, 'pdf_name': 'BSW Wahlprogramm 2025.pdf', 'title': 'Beste Bildung für alle, von der Küste bis zu den Alpen!', 'url': 'data/bsw/BSW Wahlprogramm 2025.pdf#page=23'}, {'id': 'BSW Wahlprogramm 2025.pdf_Beste Bildung für alle, von der Küste bis zu den Alpen!_1', 'page': 23, 'pdf_name': 'BSW Wahlprogramm 2025.pdf', 'title': 'Beste Bildung für alle, von der Küste bis zu den Alpen!', 'url': 'data/bsw/BSW Wahlprogramm 2025.pdf#page=23'}, {'id': 'BSW Wahlprogramm 2025.pdf_Präambel_0', 'page': 2, 'pdf_name': 'BSW Wahlprogramm 2025.pdf', 'title': 'Präambel', 'url': 'data/bsw/BSW Wahlprogramm 2025.pdf#page=2'}]}, 'total': 85.0}}
    print(final_score)

    final_score = dict(sorted(final_score.items(), key=lambda item: item[1]['total'], reverse=True))
    global saved_final_score
    saved_final_score = final_score

@app.callback(
    Output({'type': 'position-output', 'index': MATCH}, 'children'),
    Input({'type': 'recalculate-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'position-input', 'index': ALL}, 'value'),
    State({'type': 'topic-input', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def recalculate_analysis(n_clicks, positions, topics):
    if n_clicks == 0:
        return dash.no_update

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    topic, party = eval(button_id)['index'].split('_')

    position = positions[topics.index(topic)]

    threading.Thread(target=perform_recalculation, args=(party, topic, position)).start()

    # Update the UI with the loading animation
    return loading_animation

def perform_recalculation(party, topic, position):
    max_answer_length = 600
    output = []
    analysis_thread = threading.Thread(target=perform_analysis,
                                       args=([party], [topic], [position], max_answer_length, output))
    analysis_thread.start()
    analysis_thread.join()

    final_score = output[0]
    print(final_score)
    global saved_final_score
    saved_final_score[party][topic] = final_score[party][topic]
    saved_final_score[party] = voting_aid_methods.get_party_total_score(saved_final_score[party], [k for k in saved_final_score[party].keys() if k != 'total'])
    saved_final_score = dict(sorted(saved_final_score.items(), key=lambda item: item[1]['total'], reverse=True))
    pass

@app.callback(
    Output('final-score-output', 'children', allow_duplicate=True),
    Input('final-score-store', 'data'),
    prevent_initial_call=True
)
def update_ui(final_score):
    if final_score is None:
        print("Empty")
        return dash.no_update
    print("Success")
    return get_party_boxes(final_score)


@app.server.route('/local-files/<path:filename>')
def serve_local_file(filename):
    return send_from_directory(os.getcwd(), filename)


if __name__ == '__main__':
    try:
        app.run_server(debug=True)
    except OSError as e:
        print(f"An error occurred: {e}")