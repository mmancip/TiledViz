# Baselines SAST

Ce dossier contient les fichiers JSON de reference utilises pour comparer
les nouveaux scans Bandit et Semgrep.

Fichiers attendus :

- `bandit.json`
- `semgrep.json`

Principe :

- le workflow produit les JSON courants dans `security_audit/out/`
- s'il trouve une baseline correspondante ici, il genere un diff
- `--fail-on-new` fait echouer le job si de nouveaux findings apparaissent

Au premier deploiement, ce dossier peut rester sans baseline : le workflow
fera simplement les scans et publiera les artefacts.
