#!/usr/bin/env python3
"""Atualiza a seção de projetos do README do perfil GitHub.

Uso:
    python scripts/update_projects.py [--readme README.md] [--dry-run] [--include-private]

Requer a variável de ambiente GH_TOKEN (PAT com escopo repo).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
PROFILE_REPO = "AndersonMohamed/AndersonMohamed"
MAX_ITEMS = 12
START_MARKER = "<!-- PROJECTS:START -->"
END_MARKER = "<!-- PROJECTS:END -->"


def fetch_repos(token):
    """Busca todos os repositórios do usuário (paginação via header Link)."""
    repos = []
    url = f"{API}/user/repos?per_page=100&affiliation=owner&sort=pushed"
    while url:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "update_projects.py",
            },
        )
        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            sys.exit(f"erro: falha ao buscar repositórios ({e.code} {e.reason})")
        with resp:
            body = json.load(resp)
            link = resp.headers.get("Link", "")
        repos.extend(body)
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1 : part.find(">")]
                break
    return repos


def build_table(repos, include_private):
    """Filtra, ordena e monta a tabela Markdown da seção de projetos."""
    rows = []
    for r in repos:
        if r.get("fork") or r.get("archived"):
            continue
        if r.get("full_name") == PROFILE_REPO:
            continue
        if r.get("private") and not include_private:
            continue
        rows.append(r)
    rows.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)

    shown = rows[:MAX_ITEMS]
    extra = len(rows) - MAX_ITEMS

    lines = ["| Projeto | Descrição | Stack |", "| --- | --- | --- |"]
    for r in shown:
        name = r.get("name") or "?"
        if r.get("private"):
            cell = f"🔒 {name}"
        else:
            cell = f"[{name}](https://github.com/{r.get('full_name')})"
        desc = (r.get("description") or "").strip()
        desc = desc.replace("\n", " ").replace("|", "\\|")
        desc = desc or "—"
        lang = r.get("language") or "—"
        lines.append(f"| {cell} | {desc} | {lang} |")
    if extra > 0:
        lines.append("")
        lines.append(f"… e mais {extra} projetos")
    return "\n".join(lines)


def update_readme(path, table, dry_run):
    """Substitui o conteúdo entre os marcadores, mantendo-os. Idempotente."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if START_MARKER not in content or END_MARKER not in content:
        sys.exit(
            f"erro: marcadores {START_MARKER} / {END_MARKER} não encontrados em {path}"
        )
    start_idx = content.index(START_MARKER) + len(START_MARKER)
    end_idx = content.index(END_MARKER)
    new_content = content[:start_idx] + "\n" + table + "\n" + content[end_idx:]
    if new_content == content:
        print("sem mudanças (README já atualizado)")
        return
    if dry_run:
        print(table)
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print(f"README atualizado: {path}")


def main():
    # Garante saída UTF-8 mesmo em consoles Windows (cp1252) ao imprimir emojis.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Atualiza a seção de projetos do README do perfil GitHub."
    )
    parser.add_argument(
        "--readme", default="README.md", help="caminho do README (default: README.md)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="imprime o bloco gerado no stdout sem gravar no arquivo",
    )
    parser.add_argument(
        "--include-private",
        action="store_false",
        default=True,
        help="desativa a inclusão de repositórios privados "
        "(default: incluir como '🔒 nome' sem link)",
    )
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("erro: variável de ambiente GH_TOKEN não definida")

    repos = fetch_repos(token)
    table = build_table(repos, args.include_private)
    if args.dry_run:
        print(table)
        return
    update_readme(args.readme, table, dry_run=False)


if __name__ == "__main__":
    main()