# Storage

Dieses Verzeichnis ist fuer lokale Laufzeitdaten vorgesehen.

Erwartete Unterordner:

- `trainingsdaten/<ticker>/` fuer Modell, Scaler, Metadaten und Log
- `classical/<source>/` fuer Baseline- und Random-Forest-Artefakte
- `plots/` falls spaeter gespeicherte Diagramme abgelegt werden sollen
- `yfinance-cache/` fuer lokale Paket-Caches, damit Datenabrufe reproduzierbar im Projektordner bleiben

Die eigentlichen Modellartefakte sind in Git ignoriert.
