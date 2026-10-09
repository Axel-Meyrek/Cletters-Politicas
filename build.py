#!/usr/bin/env python3
"""Genera las paginas legales de Cletters a partir de los textos de la app.

Uso: python3 build.py /ruta/a/Cletters
Lee CLPrivacyPolicy.swift y CLGuidelines.swift para que la web diga exactamente lo mismo que la app.
"""
import html
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
components = repo / "Packages/CLettersKit/Sources/CLettersDesignSystem/Components"
out = Path(__file__).parent / "docs"
email = re.search(r'email = "([^"]+)"', (components / "CLLegalDocument.swift").read_text()).group(1)

STRING = r'String\(localized: "((?:[^"\\]|\\.)*)"'


def unescape(text):
    return text.replace("\\n", "\n").replace('\\"', '"')


def parse(name):
    source = (components / name).read_text()
    title = unescape(re.search(r"title: " + STRING, source).group(1))
    updated = unescape(re.search(r"updated: " + STRING, source).group(1))
    note = unescape(re.search(r"contactNote: " + STRING, source).group(1))
    sections = [
        (unescape(t), unescape(b))
        for t, b in re.findall(r"Section\(\s*title: " + STRING + r".*?\),\s*body: " + STRING, source, re.S)
    ]
    return title, updated, sections, note


def body_html(text):
    blocks, bullets = [], []
    for line in text.split("\n"):
        if line.startswith("• "):
            bullets.append(f"<li>{html.escape(line[2:])}</li>")
        else:
            if bullets:
                blocks.append("<ul>" + "".join(bullets) + "</ul>")
                bullets = []
            blocks.append(f"<p>{html.escape(line)}</p>")
    if bullets:
        blocks.append("<ul>" + "".join(bullets) + "</ul>")
    return "\n".join(blocks)


def page(title, content, active):
    nav = "".join(
        f'<a href="{href}"{" aria-current=page" if href == active else ""}>{label}</a>'
        for href, label in [("./", "Soporte"), ("privacidad.html", "Privacidad"), ("normas.html", "Normas")]
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Cletters</title>
<link rel="icon" href="icon.png">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <a class="brand" href="./"><img src="icon.png" alt="" width="40" height="40">Cletters</a>
  <nav>{nav}</nav>
</header>
<main>
{content}
</main>
<footer>Cletters · <a href="mailto:{email}">{email}</a></footer>
</body>
</html>
"""


def contact(note):
    return f'<section class="card"><h2>Contacto</h2><p>{html.escape(note)}</p><p><a class="mail" href="mailto:{email}">{email}</a></p></section>'


def legal(name, filename):
    title, updated, sections, note = parse(name)
    content = f"<h1>{html.escape(title)}</h1>\n<p class=updated>Actualizado el {html.escape(updated)}</p>\n"
    content += "\n".join(f"<section><h2>{html.escape(t)}</h2>{body_html(b)}</section>" for t, b in sections)
    content += "\n" + contact(note)
    (out / filename).write_text(page(title, content, filename))


SUPPORT = [
    ("No me llega el código", "Revisa la carpeta de spam o promociones. El código dura unos minutos; si caduca, pide uno nuevo desde la misma pantalla."),
    ("Olvidé mi contraseña", "En la pantalla de inicio de sesión toca «¿Olvidaste tu contraseña?». Te enviaremos un código a tu correo para crear una nueva."),
    ("Cómo eliminar mi cuenta", "En la app ve a tu perfil → Editar perfil → Cuenta → Eliminar cuenta. Se borra todo lo tuyo, fotos incluidas, en ese momento."),
    ("Cómo reportar o bloquear", "Desde el menú ··· de cualquier perfil, reseña o frase puedes reportarla o bloquear a esa cuenta. Revisamos cada reporte en menos de 24 horas."),
    ("Cómo hacer mi cuenta privada", "En Editar perfil → Privacidad. Con la cuenta privada solo te ven las personas que aceptes."),
]


def support():
    content = "<h1>Soporte</h1>\n<p class=lead>Cletters es tu diario de lecturas: reseñas, frases y lo que estás leyendo. Si tienes un problema o una duda, escríbenos y te respondemos lo antes posible.</p>\n"
    content += f'<section class="card"><h2>Escríbenos</h2><p><a class="mail" href="mailto:{email}">{email}</a></p></section>\n'
    content += "<h2 class=faq>Preguntas frecuentes</h2>\n"
    content += "\n".join(f"<section><h3>{html.escape(q)}</h3><p>{html.escape(a)}</p></section>" for q, a in SUPPORT)
    (out / "index.html").write_text(page("Soporte", content, "./"))


out.mkdir(exist_ok=True)
legal("CLPrivacyPolicy.swift", "privacidad.html")
legal("CLGuidelines.swift", "normas.html")
support()
print("Listo:", ", ".join(sorted(p.name for p in out.glob("*.html"))))
