#!/usr/bin/env python3
"""Hook PreToolUse da sessão do treinamento (ligado em sessao_template/.claude/settings.local.json).

Barra qualquer chamada de ferramenta que tente chegar ao gabarito, ao material do facilitador
ou à lista de datasets e jobs do projeto, seja qual for o formato do comando: `bq --project_id=... query`,
SQL em arquivo, Python com google-cloud-bigquery, INFORMATION_SCHEMA etc.
Fica em preparacao/ para o agente da sessão não conseguir ler a lista de termos.
Saída 2 = bloqueia e devolve o motivo (stderr) ao Claude.
"""
import json
import re
import sys

# termos que não podem aparecer em nenhum comando, caminho ou arquivo escrito
TERMOS = ["gabarito", "trama_setup", "preparacao", "preparação"]

# metadados do projeto e da região: listam os datasets (e o histórico de queries do facilitador)
PADROES = [
    r"region-[a-z0-9-]+`?\s*\.\s*`?information_schema",
    r"information_schema`?\s*\.\s*`?schemata",
    r"\blist_(datasets|jobs|projects)\b",
    r"\bbq\b[^|;&\n]*\bls\b[^|;&\n]*\s-(j|p|a)\b",
    r"\bbq\b[^|;&\n]*\bls\b[^|;&\n]*--(jobs|projects|all)\b",
    r"\bbq\b[^|;&\n]*\bshow\b[^|;&\n]*\s-j\b",
    r"\bgcloud\b[^|;&\n]*\b(alpha|beta)?\s*bq\b",
]

# `bq ls` só vale apontando para um dataset da demanda
DATASETS_OK = r"trama_(raw|legacy|silver|gold)\b"
BQ_LS = r"\bbq\b[^|;&\n]*\bls\b[^|;&\n]*"

MOTIVO = (
    "Bloqueado pela trava do treinamento: fora do escopo da demanda. "
    "Use só os datasets citados no PEDIDO.md (trama_raw, trama_legacy, trama_silver, trama_gold) "
    "e só os arquivos desta pasta. Se faltar informação, pergunte a quem está conduzindo."
)


def bloquear():
    print(MOTIVO, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    entrada = evento.get("tool_input") or {}
    texto = json.dumps(entrada, ensure_ascii=False).lower()

    if any(t in texto for t in TERMOS):
        bloquear()
    if any(re.search(p, texto) for p in PADROES):
        bloquear()

    comando = str(entrada.get("command", "")).lower()
    for trecho in re.findall(BQ_LS, comando):
        if not re.search(DATASETS_OK, trecho):
            bloquear()

    sys.exit(0)


if __name__ == "__main__":
    main()
