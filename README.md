# TO DO
- Riscrivere file README.md in inglese ed in sezioni, in particolare:
  - Sezione IBM
    - Main IBM
    - Funzioni IBM
  - Sezione DWAVE
    - Main DWAVE
    - Funzioni DWAVE
  - Sezione funzioni & strutture di appoggio
- Riscrivere file (riorganizza e in inglese)
  - IBM main
  - IBM funzioni
  - DWAVE main
  - DWAVE funzioni
  - funzioni & strutture

# Info
Questo branch offre una decomposizione del programma in classi e funzioni.

## fun_lib.py
Inn questo file sono implementate le classi di proxy e alcune funzioni di supporto

### Proxytree
Questa classe sostituisce totalmente la generazione dell'albero e la definizione di tutte le sue costanti

### Proxymanager
Questa classe sostituisce totalmente le costanti di gestione come la scelta di salvataggio, caricamento, moltiplicatori di tempo per i solver e i moltiplicatori di lagrange

## models.py
In questo file sono implementate tutte le funzioni legate ai solver e alla libreria D-Wave, oltre che le funzioni per costruire i vari modelli

### vm_model() & path_model()
Creano dei problemi CQM per i problemi di vm e path, il path model richiede la best solution del problema vm

### cqm_solver() & bqm_solver()
Svolgono tutto il ciclo di risoluzione di CQM/BQM

### check_bqm_feasible()
Controlla la fattibilità di una soluzione BQM dato un CQM e un inverter
