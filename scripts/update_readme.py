#!/usr/bin/env python3
"""Atualiza as seções dinâmicas do README do perfil GitHub.

Gera, a partir do perfil do GitHub (nome, bio, localização) e dos repositórios:
  - a animação do topo (Typing SVG);
  - a seção "Sobre mim";
  - a lista de projetos;
  - os banners do topo (assets/banner-light.svg e assets/banner-dark.svg).

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
from xml.sax.saxutils import escape

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
BANNER_TEMPLATES = {
    "assets/banner-light.svg": "scripts/templates/banner-light.svg.tpl",
    "assets/banner-dark.svg": "scripts/templates/banner-dark.svg.tpl",
}
BANNER_SUBTITLE_FALLBACK = "Desenvolvedor"
BANNER_MAX_SUBTITLE_CHARS = 68


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


def build_banners(profile, dry_run=False):
    """Gera os banners do topo (SVG) a partir do perfil.

    Substitui os placeholders dos templates (nome, subtítulo, cursor e linha
    terminal) e grava apenas quando o conteúdo muda (idempotente). Retorna a
    lista de arquivos alterados (ou que seriam alterados em dry-run).
    """
    bio = (profile.get("bio") or "").strip()
    sentences = split_sentences(bio, 1)
    subtitle = (
        clamp_line(sentences[0], BANNER_MAX_SUBTITLE_CHARS)
        if sentences
        else BANNER_SUBTITLE_FALLBACK
    )
    name = (profile.get("name") or "").strip() or (profile.get("login") or "?")
    whoami = f"$ whoami → {name}"
    cursor_x = 450 + (len(subtitle) * 12) // 2 + 4

    # Escapa também aspas duplas: os textos vão em atributos (aria-label) do SVG.
    _esc = lambda v: escape(v, {'"': "&quot;"})
    values = {
        "{{NAME}}": _esc(name),
        "{{SUBTITLE}}": _esc(subtitle),
        "{{CURSOR_X}}": str(cursor_x),
        "{{WHOAMI}}": _esc(whoami),
    }

    changed = []
    for dest, template in BANNER_TEMPLATES.items():
        with open(template, encoding="utf-8") as f:
            svg = f.read()
        for key, value in values.items():
            svg = svg.replace(key, value)
        old = None
        if os.path.exists(dest):
            with open(dest, encoding="utf-8") as f:
                old = f.read()
        if old != svg:
            if not dry_run:
                with open(dest, "w", encoding="utf-8", newline="\n") as f:
                    f.write(svg)
            changed.append(dest)
    return changed


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
        print("=== BANNERS ===")
        banner_changes = build_banners(profile, dry_run=True)
        if banner_changes:
            for path in banner_changes:
                print(f"seria gravado: {path}")
        else:
            print("banners sem mudanças")
        return

    changed = [
        label
        for label, start, end in sections
        if replace_between(content, start, end, blocks[label]) != content
    ]

    if changed:
        new_content = content
        for label, start, end in sections:
            new_content = replace_between(new_content, start, end, blocks[label])

        with open(args.readme, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        print(
            f"README atualizado: {args.readme} "
            f"(seções alteradas: {', '.join(changed)})"
        )
    else:
        print("sem mudanças (README já atualizado)")

    banner_changes = build_banners(profile)
    if banner_changes:
        print(f"banners atualizados: {', '.join(banner_changes)}")
    else:
        print("banners sem mudanças")


if __name__ == "__main__":
    main()
