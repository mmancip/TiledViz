# Outils SAST JSON - Bandit & Semgrep

Inspiration : scripts `sort_json.py` / `compare_json.py` (Martial Mancip) -
**normaliser -> comparer -> rapporter**. Transposes aux JSON Bandit / Semgrep.

## Outils

| Script | Role |
|--------|------|
| `bandit_json.py` | Bandit uniquement |
| `semgrep_json.py` | Semgrep uniquement |
| `_sast_json_common.py` | Helpers partages |
| `test_sast_json.py` | Tests unitaires |

## Sous-commandes communes

| Commande | Entree | Sortie |
|----------|--------|--------|
| `normalize` | `*.json` brut | JSON stable |
| `report` | `*.json` brut ou normalise | Markdown lisible |
| `diff` | deux `*.json` (A = baseline, B = nouveau) | Markdown + code retour CI |

## Exemples

```bash
python3 security_audit/bandit_json.py report bandit.json -o bandit.md
python3 security_audit/semgrep_json.py report semgrep.json -o semgrep.md

python3 security_audit/bandit_json.py diff old.json new.json -o bandit_diff.md --fail-on-new
python3 security_audit/semgrep_json.py diff old.json new.json -o semgrep_diff.md --fail-on-new
```

## CI

- `requirements.txt` installe les scanners Python.
- Les scripts Python ici sont non interactifs et n'utilisent que la stdlib.
- `diff --fail-on-new` echoue si le nouveau run introduit des findings absents de la baseline.
- `diff --fail-on-severity` permet de bloquer a partir d'un seuil.

## Tests

```bash
cd security_audit
python3 test_sast_json.py
python3 -m unittest test_sast_json -v
```
