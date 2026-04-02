# stock-predictor

Verbessern:
- trainigsdaten im drive und nicht im projekt speichen
    --> daten werden gespeichert und sind nicht nach jeder sitzung wieder weg
- schneller berechnen können
- rsi berechnung überprüfen + was gibts noch für so ähnliche die man auch zum berechnen aufnehmen kann
- bei neuen daten nicht wieder neu anfangen sondern weitermachen wo aufgehört wurde
    --> erst chati fragen ob das nicht schon drin ist
- neben steigung evtl noch der durchschnittliche preisabstand zum letzten wert des realen kurses
- training machen dass aus allen sachen gelernt wird und nicht immer jede aktie einzeln
- ETFs miteinbinden
- grid-trading funktioniert gut
- meta trader / pinescript --> trading view (besser)
- machen dass die Ergebnisse als Werte zusammengesetzt bzw addiert werden
    --> Unternehmen sollen nach höhe des Wertes sortiert werden --> z.B. Steigung*10=-9,2... + (100-RSI)*0,2 + ... = 7,2

WICHTIG:
- Modelle persistent/permanent speichern
- mehrere Kurse gleichzeitig betrachten und dann ein Unternehmensranking erstellen

Wenn alles klappt:
- preise an den punkten der predictions anzeigen
- diese bars wenn trainiert wird nach dem training ausblenden oder generell eine bessere art das training zu visualisieren
- eventuelle einbindung von nachrichten für bestimmte kurse die man predicted haben will
    --> falls die halt fallen oder steigen oder so je nachdem was man wissen will
- wird schwer umzusetzen
    --> nur prediciton nicht in tage sondern in stunden aber dennoch tage angeben
- ungefähre dauer bis das programm fertig ist
