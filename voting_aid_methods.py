import llm_api_wrapper
import query_data
import concurrent.futures

def get_summary_instructions():
    return (
        "Erstelle eine Liste der zentralen Themengebiete, die in diesen politischen Positionen behandelt werden. "
        "Die Themengebiete sollten abstrakt und allgemein gehalten sein. Berücksichtige alle Hauptthemen, "
        "die im Text angesprochen werden. Es soll keine Überschneidungen geben. "
        "Dabei ist es erwünscht das diese Überpunkte weiterhin eine Aussage treffen "
        "(also Worte wie 'will', 'glaube' und 'soll' sind erwünscht).\n"
        "Fasse die politischen Positionen zu jedem identifizierten Thema zusammen. "
        "Gliedere die Meinungen in Stichpunkten. Beziehe dich ausschließlich auf die politischen Positionen. "
        "Achte darauf, dass es sich nicht mit den anderen Themen überschneidet. "
        "Gebe Stichpunkte direkt untereinander an ohne leere Zeilen zwischen den Stichpunkten. "
        "Interpretiere die politischen Positionen nicht, sondern fasse sie nur zusammen. "
        "Sollte die Meinung nicht weiter spezifiziert werden, dann kannst du die Stichpunkte weglassen."
        "---"
        "Hier sind Beispiele, wie die Ausgabe aussehen könnte: \n"
        "**Beispiel 1:** \n"
        "Input: \n"
        "Ich finde, dass Bildung stärker gefördert werden sollte, da sie der Schlüssel zu sozialem und "
        "wirtschaftlichem Fortschritt ist.Kostenlose oder erschwingliche Bildung für alle sollte oberste Priorität "
        "haben, um Chancengleichheit zu gewährleisten und langfristig soziale Ungleichheiten abzubauen.\n"
        "Output: \n"
        "Bildung für alle – Schlüssel zur Zukunft! \n"
        "* Bildung ist essenziell für sozialen und wirtschaftlichen Fortschritt. \n"
        "* Kostenlose oder erschwingliche Bildung soll für alle zugänglich sein. \n"
        "* Förderung von Chancengleichheit durch Bildung. \n"
        "\n\n"
        "**Beispiel 2:** \n"
        "Input: \n"
        "Eine gerechtere Gesellschaft und ein nachhaltiger Umgang mit unseren Ressourcen sind zentrale "
        "Herausforderungen unserer Zeit.Um soziale Gerechtigkeit zu fördern, sollte der gesetzliche Mindestlohn "
        "regelmäßig an die Inflation angepasst werden, damit Menschen von ihrer Arbeit leben können.Zusätzlich "
        "ist eine Reform der Besteuerung notwendig, bei der Spitzenverdiener und große Unternehmen stärker zur "
        "Finanzierung sozialer Projekte wie bezahlbarem Wohnraum oder einer besseren Gesundheitsversorgung "
        "herangezogen werden.Familien könnten durch den Ausbau kostenfreier Kitas und Ganztagsschulen entlastet "
        "werden, was die Vereinbarkeit von Beruf und Familie deutlich verbessert.\n"
        "Gleichzeitig muss der Klimaschutz in den Fokus rücken.Die Förderung erneuerbarer Energien, wie Solar- und "
        "Windkraft, sollte durch staatliche Subventionen vorangetrieben werden, ergänzt durch Programme zur "
        "Entwicklung von Energiespeichern.Eine Mobilitätswende kann durch den Ausbau des öffentlichen Nahverkehrs "
        "gelingen, etwa durch dichtere Taktungen und ein günstiges 1-Euro-Ticket pro Tag.Um Ressourcen zu schonen, "
        "sollten verbindliche Recyclingquoten für Unternehmen eingeführt und Reparatur- sowie "
        "Wiederverwendungsinitiativen stärker gefördert werden.Diese Maßnahmen schaffen die Grundlage für eine "
        "gerechtere und nachhaltigere Zukunft.\n"
        "Output: \n"
        "Mehr Soziale Gerechtigkeit! \n"
        "* Erhöhung des Mindestlohns: Der gesetzliche Mindestlohn sollte an die Inflation gekoppelt und regelmäßig angepasst werden,"
        " um Kaufkraftverluste auszugleichen.\n"
        "* Reform der Besteuerung: Einführung einer stärkeren Besteuerung von Spitzenverdienern und großen Unternehmen, um soziale "
        "Projekte wie bezahlbaren Wohnraum oder Gesundheitsversorgung zu finanzieren.\n"
        "* Familienförderung: Ausbau von kostenfreien Kitas und Ganztagsschulen, um Beruf und Familie besser vereinbaren zu können.\n"
        "\n\n"
        "Nachhaltigkeit und Klimaschutz"
        "* Förderung erneuerbarer Energien: Staatliche Subventionen für Solar- und Windkraft sowie Programme zur "
        "Förderung von Energiespeichern.\n"
        "* Mobilitätswende: Ausbau des öffentlichen Nahverkehrs durch höhere Taktung und Vergünstigung von "
        "Tickets, ideal wäre ein 1-Euro-Ticket pro Tag.\n"
        "* Kreislaufwirtschaft: Einführung verbindlicher Recyclingquoten für Unternehmen und stärkere Förderung von "
        "Reparatur- und Wiederverwendungsinitiativen."
        "\n\n"
        "**Beispiel 3:** \n"
        "Input: \n"
        "Die Cannabis Legalisierung ist gut.\n"
        "Output: \n"
        "Die Cannabis Legalisierung ist richtig!"
        "\n\n"
        "Nutze diese Struktur, um die Themen im folgenden Text zu identifizieren. Achte darauf die Themen klar mit "
        "zwei break lines zu trennen.\n"
        "Fasse auch nur die positionen zusammen und achte darauf das kein Interpretationsspielraum bleibt."
        "So wäre bei Beispiel 1 der Unterpunkt 'Langfristige Reduktion sozialer Ungleichheiten.' fehl am Platz, da "
        "das mehr eine Erklärung der Position ist. Man könnte hier schließlich die Annahme treffen, dass die Person "
        "für eine Umverteilung ist, was nicht in der Position steht."
        "Bei Beispiel 3 wurden keine weiteren Stichpunkte angegeben, da die Position nicht weiter spezifiziert "
        "wurde. In diesem Fall darf auf keinen Fall etwas in die position interpretiert werden. Die Aussage sagt "
        "z.B. nicht das man eine fortschrittliche Drogen Politik befürwortet."
    )

def get_criteria_instructions():
    return (
        "Du wirst eine politische Position zu einem Thema erhalten. \n"
        "Erläutere was im Kontext deutsche Politik 0%, 20%, 40%, ..., 100% Übereinstimmung bedeuten würde. "
    )

def get_rag_prompt_template():
    return \
        """ Hier ist meine politische Position zu einem Thema: {question}
        ---
        Hier ist die politische Position einer Partei: {context}
        ---
        Wie eng entspricht meine Meinung in der Frage, die der Partei? Bewerte von 0-100!
        """

def get_rag_rating_instructions(topic_criteria, max_answer_length=100):
    return (
        f"Wie eng entspricht meine Meinung dem der Partei? Antworte in {max_answer_length} Zeichen oder weniger. "
        f"und bewerte von 0-100."
        f"Nutze diese Kriterien um die Antwort zu bewerten: {topic_criteria}"
        f"\n---\n"
        f"Antworte bitte im folgenden Format:\n"
        f"Antwort: <detaillierte Antwort>\n"
        f"Bewertung: <Zahl>\n"
        f"---\n"
        f"Sollten die Abschnitte aus dem Parteiprogramm keinen Zusammenhang zu meiner Meinung haben, "
        f"dann antworte ausschließlich mit: 'None'."
        f"Deine Antwort darf sich ausschließlich auf den Inhalt der politischen Positionen im Abschnitt des "
        f"Parteiprogramms beziehen. Zögere nicht mit 'None' zu antworten, wenn du keine Übereinstimmung siehst."
        f"Antworte auf keinen Fall mit deinem Wissen über die Partei. Die Antwort muss sich ausschließlich auf den "
        f"Text beziehen."
    )

def is_rating_sufficient_instruction():
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist politische Meinungen von einer Partei mit meiner Meinung zu "
        "vergleichen. Glaubst du die Partei wurde anhand von Abschnitten aus ihrem Parteiprogramm und der "
        "Bewertungskriterien richtig bewertet? Das Ergebnis der Bewertung steht im Score."
        "Beachte das eine Bewertung von '-1' oder 'None' bedeutet das der Abschnitt nicht ausreichend war."
        "Glaubst du die Abschnitte aus dem Parteiprogramm sind ausreichend um die Fragestellung zu beantworten? "
        "\n---\n"
        "Sollten die Abschnitte nicht ausreichen dann genügt eine Antwort mit: 'Die Abschnitte sind nicht ausreichend.'"
        "Es ist dann egal ob die Partei richtig oder falsch bewertet wurde.\n"
        "Antworte ausschließlich mit einer dieser Optionen: \n"
        "Die Abschnitte sind nicht ausreichend. \n"
        "Die Partei wurde nicht richtig bewertet. Die Abschnitte sind aber ausreichend.\n"
        "Die Partei wurde richtig bewertet und Die Abschnitte sind ausreichend.\n"
    )

def get_reevaluate_rating_instructions():
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist meine politische Meinung mit der Meinung von einer Partei zu "
        "vergleichen. Ein anderer Agent hat den Score anhand der Abschnitte  und der Bewertungskriterien "
        "als falsch bewertet eingestuft. Passe die Bewertung bitte an. \n"
        "Antworte bitte im folgenden Format:\n"
        "Antwort: <detaillierte Antwort>\n"
        "Bewertung: <Zahl>\n"
    )

def is_context_completely_instructions():
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist meine politische Meinung mit der Meinung von einer Partei zu "
        "vergleichen. Ein anderer Agent hat die Abschnitte aus dem Parteiprogramm als nicht ausreichend eingestuft. "
        "Die Abschnitte werden von einer RAG-DB bezogen. Beinhalten die Abschnitte bzw. der Score einen Teil der "
        "Antwort? oder sind die Abschnitte komplett falsch? \n"
        "Antworte ausschließlich mit einer dieser Optionen: \n"
        "Die Abschnitte und der Score sind nicht ausreichend aber zu teilen Richtig bzw. Relevant. \n"
        "Die Abschnitte und der Score sind komplett falsch. \n"
    )

def get_adapted_opinion_for_better_context_instructions(max_answer_length=100):
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist meine politische Meinung mit der Meinung von einer Partei zu "
        "vergleichen. Ein anderer Agent hat die Abschnitte aus Parteiprogrammen als nicht ausreichend eingestuft. "
        "Die Abschnitte werden von einer RAG-DB bezogen. Passe meine politische Meinung so an, dass die RAG-DB mehr "
        "zu dem Thema finden kann. Dazu kannst du schon gefundene Themen, entfernen. \n"
        "Passe auf keinen Fall den Inhalt an sondern ausschließlich das Vokabular. "
        "Antworte ausschließlich mit meiner überarbeiteten politischen Meinung!"
        f"Antworte in {max_answer_length} Zeichen oder weniger"
    )

def get_adapted_opinion_for_new_context_instructions(max_answer_length=100):
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist meine politische Meinung mit der Meinung von einer "
        "Partei zu vergleichen. Ein anderer Agent hat die Abschnitte aus dem Parteiprogramm als falsch eingestuft. "
        "Die Abschnitte werden von einer RAG-DB bezogen. Passe meine politische Meinung so an, dass die RAG-DB "
        "mehr zu dem Thema finden kann. \n"
        "Passe auf keinen Fall den Inhalt an sondern ausschließlich das Vokabular. "
        "Antworte ausschließlich mit meiner überarbeiteten politischen Meinung!"
        f"Antworte in {max_answer_length} Zeichen oder weniger"
    )

def get_rating_from_response_instructions():
    return (
        "Ich habe einen Agenten, dessen Aufgabe es ist meine politische Meinung mit der Meinung von einer Partei zu "
        "vergleichen. Der Agent hat keine Zahl als Bewertung ausgespuckt. Bitte bewerte den Score von 0-100. "
        "Antworte nur mit einer Zahl, es sei denn du bist der Meinung das die Antwort nicht bewertbar ist. "
        "Dann antworte mit: 'Die Antwort ist nicht bewertbar.'"
    )


def get_topics_and_descriptions(political_position):
    response = llm_api_wrapper.basic_prompt(political_position, get_summary_instructions(), temperature=0)
    topics_and_positions = response.split("\n\n")

    topics = []
    positions = []
    for tp in topics_and_positions:
        if tp.strip():
            parts = tp.split("\n", 1)
            topics.append(parts[0])
            if len(parts) > 1:
                positions.append(parts[1])
            else:
                positions.append("")

    return topics, positions


def get_topic_criteria(topic, position):
    position_text = "Thema: " + topic + "\n Politische Position" + position
    criteria = llm_api_wrapper.basic_prompt(position_text, get_criteria_instructions(), temperature=0.1)
    # print(f"Criteria:\n {criteria}")
    return criteria


def get_party_context_of_political_position_npp(party, position_text, topic_criteria, max_answer_length=100):
    response, context, metadata = query_data.query_rag(position_text, party,
                                                        get_rag_rating_instructions(topic_criteria, max_answer_length),
                                                        get_rag_prompt_template())
    score = {}
    if response != "None":
        try:
            detailed_answer, rating = split_response(response)
        except:
            detailed_answer = None
            rating = -1
    else:
        detailed_answer = None
        rating = -1

    for m in metadata:
        if "url" not in m:
            if "pdf_name" in m:
                m["url"] = f"data/{party}/{m['pdf_name']}"
                if m["page"] != -1:
                    m["url"] += f"#page={m['page']}"

    score["detailed_answer"] = detailed_answer
    score["rating"] = int(rating) if  str(rating).isdigit() else None
    score["metadata"] = metadata
    return score, context

def get_party_context_of_political_position(party, topic, position, topic_criteria, max_answer_length=100,
                                            recursive_depth=0):
    if recursive_depth == 0:
        position_text = "Thema: " + topic + "\n Politische Position: " + position
    else:
        position_text = position
    score, context = get_party_context_of_political_position_npp(party, position_text, topic_criteria, max_answer_length)
    return analyze_score(score, position_text, context, party, topic_criteria, recursive_depth)

def analyze_score(score, position, context, party, topic_criteria, recursive_depth=0):
    max_recursive_depth = 3
    p_pcs = ("Meine Politische Meinung: \n" + position + "\n---\n"
             + "Abschnitte aus dem Parteiprogramm: \n" + context + "\n---\n"
             + "Bewertung: " + str(score["rating"]))

    if ("detailed_answer" in score and "rating" in score and score["detailed_answer"] is not None
            and score["rating"] is not None):

        response = llm_api_wrapper.basic_prompt(p_pcs, is_rating_sufficient_instruction())
        if "wurde richtig bewertet" in response.lower():
            return score
        elif "wurde nicht richtig bewertet" in response.lower():
            response = llm_api_wrapper.basic_prompt(p_pcs, get_reevaluate_rating_instructions())

            # Extract the score from the response
            detailed_answer, rating = split_response(response)
            score["detailed_answer"] = detailed_answer
            score["rating"] = int(rating) if str(rating).isdigit() else 0
            if recursive_depth < max_recursive_depth:
                return analyze_score(score, position, context, party, topic_criteria, recursive_depth + 1)
            else:
                return score
        elif "abschnitte sind nicht ausreichend" in response.lower() and party != "bsw":
            response = llm_api_wrapper.basic_prompt(p_pcs, is_context_completely_instructions())

            if "zu teilen richtig" in response.lower():
                    response = llm_api_wrapper.basic_prompt(p_pcs, get_adapted_opinion_for_better_context_instructions())
                    new_score, new_context = get_party_context_of_political_position_npp(party, response, topic_criteria)

                    prompt = ("Politische Meinung: " + position + "\n---\n"
                                + "Bewertung 1: " + str(score) + "\n---\n"
                                + "Bewertung 2: " + str(new_score))
                    response = llm_api_wrapper.basic_prompt(prompt, get_rag_prompt_template())

                    # Extract the score from the response
                    detailed_answer, rating = split_response(response)
                    score["detailed_answer"] = detailed_answer
                    score["rating"] = int(rating) if rating and rating.isdigit() else -1
                    if recursive_depth < max_recursive_depth:
                        return analyze_score(score, position, (context+new_context), party, topic_criteria, recursive_depth + 1)
                    else:
                        return score
            elif "komplett falsch" in response.lower():
                response = llm_api_wrapper.basic_prompt(p_pcs, get_adapted_opinion_for_new_context_instructions())
                if recursive_depth < max_recursive_depth:
                    return get_party_context_of_political_position(party, "", response, topic_criteria, recursive_depth + 1)
                else:
                    return score
            else:
                # print("Invalid response")
                # print(response)
                return score
        else:
            # print("Invalid response")
            # print(response)
            return score
    elif "detailed_answer" not in score or score["detailed_answer"] is None:
        response = llm_api_wrapper.basic_prompt(p_pcs, get_adapted_opinion_for_new_context_instructions())
        if recursive_depth < max_recursive_depth:
            return get_party_context_of_political_position(party, "", response, topic_criteria, recursive_depth + 1)
        else:
            return score
    else:
        response = llm_api_wrapper.basic_prompt(p_pcs, get_rating_from_response_instructions())
        if response.isdigit():
            score["rating"] = int(response)
            return analyze_score(score, position, context, party, topic_criteria, recursive_depth+1)
        else:
            response = llm_api_wrapper.basic_prompt(p_pcs, get_adapted_opinion_for_new_context_instructions())
            if recursive_depth < max_recursive_depth:
                return get_party_context_of_political_position(party, "", response, topic_criteria, recursive_depth + 1)
            else:
                return score

def get_criteria_for_position(index, topics, positions):
    return get_topic_criteria(topics[index], positions[index])

def process_position(i, party, topics, positions, criteria, max_answer_length):
    result = get_party_context_of_political_position(party, topics[i], positions[i], criteria[i], max_answer_length)
    # print(f"Die {party} ist in dem Thema '{topics[i]}', {result['rating']}% an deiner Meinung.")
    return topics[i], result

def process_party(party, topics, positions, criteria, max_answer_length):
    party_score = {}
    for topic in topics:
        party_score[topic] = None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_position, i, party, topics, positions, criteria, max_answer_length) for i in range(len(positions))]
        for future in concurrent.futures.as_completed(futures):
            topic, result = future.result()
            party_score[topic] = result

    party_score["total"] = -1
    valid_ratings = [int(party_score[topic]['rating']) for topic in topics
                     if party_score[topic]['detailed_answer'] is not None and party_score[topic]['rating'] != -1]
    if len(valid_ratings) > 0:
        baseline_score = 15
        party_score["total"] = sum(valid_ratings) / len(valid_ratings)
        if party_score["total"] > baseline_score:
            valid_ratings = [int(party_score[topic]['rating']) for topic in topics
                             if party_score[topic]['detailed_answer'] is not None]
            valid_ratings = [r if r != -1 else baseline_score for r in valid_ratings]
            party_score["total"] = sum(valid_ratings) / len(valid_ratings)
    # print(f"Die {party} ist in deiner politischen Position, {party_score['total']}% an deiner Meinung.")
    # print()
    return party, party_score

def get_parties_context_of_political_positions(parties, topics, positions, max_answer_length=100):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        criteria_futures = [executor.submit(get_criteria_for_position, i, topics, positions) for i in range(len(positions))]
        criteria = [future.result() for future in concurrent.futures.as_completed(criteria_futures)]

    score = {}
    for party in parties:
        score[party] = None
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_party, party, topics, positions, criteria, max_answer_length) for party in parties]
        for future in concurrent.futures.as_completed(futures):
            party, party_score = future.result()
            score[party] = party_score

    return score

def split_response(response):
    parts = response.split("\nBewertung: ")
    detailed_answer = parts[0].replace("Antwort: ", "").strip()
    rating = parts[1].strip() if len(parts) > 1 else None
    return detailed_answer, rating