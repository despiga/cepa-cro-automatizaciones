# -*- coding: utf-8 -*-
"""CSS común de los reportes (tokens claro/oscuro, tipografía, tarjetas y tablas).
Cada script agrega solo lo propio con el parámetro `extra`."""

FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">')

_CLARO = ('--bg:#F3F5F7;--card:#FFFFFF;--ink:#1B2630;--mut:#5B6670;--line:#DDE3E8;--navy:#17324D;--acc:#B4531A;--warnbg:#FDF1E7;'
          '--v1:#1F5F8B;--v2:#B4531A;--v3:#4F8A5B;--v4:#7A4E9C;--v5:#9C7A1F;--trk:#E7ECF0;'
          "--hf:'Space Grotesk',Arial,sans-serif;--bf:'Inter',Arial,sans-serif")
_OSCURO = ('--bg:#0F1A24;--card:#16232F;--ink:#E6ECF1;--mut:#9AA8B4;--line:#2A3A48;--navy:#9CC3E6;--acc:#E39358;--warnbg:#2A1E15;'
           '--v1:#6AAEDC;--v2:#E39358;--v3:#7DBB89;--v4:#B994D6;--v5:#D9B95C;--trk:#22323F;color-scheme:dark')


def css(ancho=960, card_pad='18px 20px', tabla_min=520, extra=''):
    return (
        f':root{{{_CLARO}}}\n'
        f'@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{_OSCURO}}}}}\n'
        f':root[data-theme="dark"]{{{_OSCURO}}}\n'
        'body{background:var(--bg);color:var(--ink);font:14px/1.5 var(--bf);padding-block:24px;'
        'padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}\n'
        f'.wrap{{max-width:{ancho}px;margin:0 auto;display:flex;flex-direction:column;gap:18px}}\n'
        'h1{font:700 28px/1.15 var(--hf);color:var(--navy);margin:0;text-wrap:balance}\n'
        'h2{font:700 17px var(--hf);color:var(--navy);margin:0 0 4px}\n'
        'h3{font:700 15px var(--hf);color:var(--navy);margin:0 0 4px}\n'
        '.sub{color:var(--mut);margin:4px 0 0}\n'
        f'.card{{background:var(--card);border:1px solid var(--line);padding:{card_pad};min-width:0}}\n'
        '.note{background:var(--warnbg);border-left:3px solid var(--acc);padding:12px 16px}.note b{color:var(--acc)}\n'
        '.delta{background:var(--card);border:1px solid var(--line);padding:10px 16px;font-size:13px;color:var(--mut)}.delta b{color:var(--navy)}\n'
        f'.tw{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;min-width:{tabla_min}px}}\n'
        'th{text-align:left;font:600 12px var(--bf);color:var(--mut);letter-spacing:.04em;text-transform:uppercase;padding:6px 8px;border-bottom:1px solid var(--line)}\n'
        'td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}td a{color:var(--navy)}\n'
        '.num{text-align:right;font-variant-numeric:tabular-nums}th.num{text-align:right}\n'
        '.mut{color:var(--mut)}.warn,td.warn{color:var(--acc)}\n'
        'small{color:var(--mut)}ul{margin:6px 0 0;padding-left:20px}li{margin:0 0 4px}\n'
        '.foot{color:var(--mut);font-size:12px}\n'
        + extra
    )


def cabecera(titulo):
    """<head> completo con título, viewport y fuentes; el <style> lo agrega cada script."""
    from html import escape as e
    return ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<title>{e(titulo)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + FUENTES)
