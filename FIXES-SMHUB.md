# Correzioni SMHstamon

Base: master, commit 8b313691b98142d3c1bd646d290e1aba60380f46.

## Problema riprodotto

Con due riquadri server, nascondere quello senza allarmi generava:
`AttributeError: 'ServerVBox' object has no attribute 'button_monitor'`.
Il pulsante era stato rimosso dall'interfaccia ma era ancora usato da
`hide_all()` e `delete()`. Corretti entrambi i riferimenti.

## Altre correzioni

- Rimane disponibile solo SMHUB; non vengono importati i backend inutilizzati
  (che introducevano anche dipendenze estranee, come pkg_resources).
- Le richieste JSON usano una sessione separata per server, il timeout configurato,
  le impostazioni proxy e TLS, senza autenticazione HTTP.
- Gli errori HTTP vengono segnalati invece di cancellare gli allarmi esistenti.
- Gli host hanno nome, server di appartenenza e stato UP correttamente inizializzati.
- Sono riconosciuti sia `unknow` sia `unknown`; le note nulle sono accettate.

## Avvio dai sorgenti

Estrarre l'archivio e aprire un terminale nella cartella estratta. Con Python 3
installato, creare preferibilmente un ambiente virtuale:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install PyQt6 requests beautifulsoup4 lxml python-dateutil keyring psutil cryptography
.\.venv\Scripts\python smhstamon.py
```

Per una prova con configurazione separata:

```powershell
.\.venv\Scripts\python smhstamon.py .\config-prova
```

L'archivio contiene sorgenti, non un nuovo eseguibile Windows compilato.
Per aggiornare una copia Git sul commit base, la patch si applica con:

```text
git apply --check SMHstamon-fix.patch
git apply SMHstamon-fix.patch
```

## Verifiche

```text
python -m unittest discover -s tests -p test_smhub.py -v
```

9 test superati su Windows con Python 3.12 e PyQt6: aggiunta di due server tramite
il dialogo reale (senza il ciclo modale), visibilita e rimozione dei riquadri,
allarmi separati anche con etichette uguali, sessione e timeout, errori HTTP,
timeout e JSON invalido, TLS e assenza di autenticazione, stato unknown e note nulle.
Le risposte HTTP sono simulate. Il test usa una configurazione temporanea e un
keyring nullo, senza modificare la configurazione personale.

Il test GUI falliva prima della correzione con l'AttributeError sopra riportato.
Non sono state testate API SMHUB di produzione o generato un nuovo eseguibile.
Nessuna modifica pubblicata su GitHub.

## Aggiornamento interfaccia

Nome visibile uniformato a SMHUB. Rimosse dai Settings le schede Filters, Actions
e Defaults e rimosso il collegamento Filters dalla barra principale. I valori
delle configurazioni esistenti vengono conservati. Verificati anche le quattro
schede rimaste e i collegamenti che usavano gli indici precedenti.
