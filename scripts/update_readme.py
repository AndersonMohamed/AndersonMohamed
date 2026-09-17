#!/usr/bin/env python3
"""Atualiza as seções dinâmicas do README do perfil GitHub.

Gera, a partir do perfil do GitHub (nome, bio, localização) e dos repositórios:
  - a animação do topo (Typing SVG);
  - a seção "Sobre mim";
  - a lista de projetos.

Uso:
    python scripts/update_readme.py [--readme README.md] [--dry-run] [--include-private]

Requer a variável de ambiente GH_TOKEN (PAT com escopo repo).
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
PROFILE_REPO = "AndersonMohamed/AndersonMohamed"
MAX_ITEMS = 12
PROJECTS_START = "<!-- PROJECTS:START -->"
PROJECTS_END = "<!-- PROJECTS:END -->"
TYPING_START = "<!-- TYPING:START -->"
TYPING_END = "<!-- TYPING:END -->"
ABOUT_START = "<!-- ABOUT:START -->"
ABOUT_END = "<!-- ABOUT:END -->"
TYPING_BASE = (
    "https://readme-typing-svg.demolab.com/?font=Fira+Code&size=20&duration=3200"
    "&pause=700&color=8B5CF6&center=true&vCenter=true&width=840"
)
TYPING_MAX_LINE_CHARS = 68
TYPING_BIO_FALLBACK = "Sempre aprendendo algo novo ✨"
TYPING_STYLE_LINES = ["Transformando ideias em código 🚀"]
ABOUT_FIXED_BULLETS = [
    "🛠️ Explorando novas linguagens e ferramentas a cada projeto",
    "🎯 Objetivo: construir soluções que façam a diferença",
]


def fetch_json(url, token):
    """Faz GET autenticado na API do GitHub e retorna (json, header Link)."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "update_readme.py",
        },
    )
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        sys.exit(f"erro: falha ao buscar {url} ({e.code} {e.reason})")
    with resp:
        return json.load(resp), resp.headers.get("Link", "")


def fetch_profile(token):
    """Busca o perfil do usuário autenticado (GET /user)."""
    body, _ = fetch_json(f"{API}/user", token)
    return body


def fetch_repos(token):
    """Busca todos os repositórios do usuário (paginação via header Link)."""
    repos = []
    url = f"{API}/user/repos?per_page=100&affiliation=owner&sort=pushed"
    while url:
        body, link = fetch_json(url, token)
        repos.extend(body)
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1 : part.find(">")]
                break
    return repos


def clamp_line(text, limit=TYPING_MAX_LINE_CHARS):
    """Corta o texto em `limit` caracteres na última fronteira de palavra + "…".

    Sem espaço antes do limite, faz o corte duro.
    """
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    if cut == -1:
        return text[:limit] + "…"
    return text[:cut].rstrip() + "…"


def split_sentences(text, max_n):
    """Divide o texto em sentenças e retorna até max_n delas."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()][:max_n]


def build_typing_img(profile):
    """Monta a tag <img> do Typing SVG com as linhas vindas do perfil."""
    name = (profile.get("name") or "").strip() or (profile.get("login") or "?")
    lines = [f"Olá! Eu sou o {name} 👋"]
    location = (profile.get("location") or "").strip()
    if location:
        lines.append(f"📍 {location}")
    bio = (profile.get("bio") or "").strip()
    if bio:
        lines.extend(clamp_line(s) for s in split_sentences(bio, 2))
    else:
        lines.append(TYPING_BIO_FALLBACK)
    lines.extend(TYPING_STYLE_LINES)
    url = TYPING_BASE + "&lines=" + ";".join(
        urllib.parse.quote(line, safe="") for line in lines
    )
    return f'  <img src="{url}" alt="Typing SVG">'


def build_about(profile):
    """Monta o bloco Markdown da seção "Sobre mim" a partir do perfil."""
    name = (profile.get("name") or "").strip() or (profile.get("login") or "?")
    bio = (profile.get("bio") or "").strip().replace("```", "``")
    location = (profile.get("location") or "").strip()
    company = (profile.get("company") or "").strip()
    blog = (profile.get("blog") or "").strip()

    lines = ["```bash", "$ whoami", name]
    if bio:
        lines.append("$ ./anderson --bio")
        lines.extend(f'"{clamp_line(s)}"' for s in split_sentences(bio, 2))
    lines.append("```")
    lines.append("")

    if location:
        lines.append(f"- 📍 **{location}**")
    if company:
        lines.append(f"- 💼 **{company}**")
    if blog:
        url = blog if "://" in blog else f"https://{blog}"
        lines.append(f"- 🔗 **[{blog}]({url})**")
    lines.extend(f"- {b}" for b in ABOUT_FIXED_BULLETS)
    return "\n".join(lines)


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


def replace_between(content, start, end, block):
    """Substitui o conteúdo entre os marcadores, preservando-os. Idempotente."""
    start_idx = content.index(start) + len(start)
    end_idx = content.index(end)
    return content[:start_idx] + "\n" + block + "\n" + content[end_idx:]


def main():
    # Garante saída UTF-8 mesmo em consoles Windows (cp1252) ao imprimir emojis.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Atualiza as seções dinâmicas do README do perfil GitHub."
    )
    parser.add_argument(
        "--readme", default="README.md", help="caminho do README (default: README.md)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="imprime os blocos gerados no stdout sem gravar no arquivo",
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

    with open(args.readme, encoding="utf-8") as f:
        content = f.read()

    sections = (
        ("TYPING", TYPING_START, TYPING_END),
        ("ABOUT", ABOUT_START, ABOUT_END),
        ("PROJECTS", PROJECTS_START, PROJECTS_END),
    )
    for label, start, end in sections:
        if start not in content or end not in content:
            sys.exit(
                f"erro: marcadores {start} / {end} não encontrados em {args.readme}"
            )

    profile = fetch_profile(token)
    repos = fetch_repos(token)

    blocks = {
        "TYPING": build_typing_img(profile),
        "ABOUT": build_about(profile),
        "PROJECTS": build_table(repos, args.include_private),
    }

    if args.dry_run:
        for label, _, _ in sections:
            print(f"=== {label if label != 'ABOUT' else 'SOBRE MIM'} ===")
            print(blocks[label])
            print()
        return

    changed = [
        label
        for label, start, end in sections
        if replace_between(content, start, end, blocks[label]) != content
    ]

    if not changed:
        print("sem mudanças (README já atualizado)")
        return

    new_content = content
    for label, start, end in sections:
        new_content = replace_between(new_content, start, end, blocks[label])

    with open(args.readme, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print(f"README atualizado: {args.readme} (seções alteradas: {', '.join(changed)})")


if __name__ == "__main__":
    main()
