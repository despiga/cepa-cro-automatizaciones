# -*- coding: utf-8 -*-
"""Utilidades compartidas por los reportes de Pipedrive (carga de datos, cotizaciones, formatos)."""
import json
import datetime as dt
from html import escape as e


def cargar_config(ruta):
    """Lee el config.json de la base (lo escribe la tarea programada a partir de su prompt)."""
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


def cargar_lista(rutas):
    """Une uno o varios JSON de respuestas de Pipedrive (rutas separadas por coma).
    Acepta tanto {"data": [...]} como una lista directa."""
    out = []
    for p in rutas.split(','):
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, dict):
            d = d.get('data', d)
        out += d or []
    return out


def cargar_fx(ruta, respaldo):
    """Devuelve (FX, FXI): FX = pesos por 1 USD por moneda; FXI = metadatos de las que vinieron en fx.json.
    Las monedas que no estén en fx.json quedan con el valor de respaldo del config."""
    FX = {k: float(v) for k, v in respaldo.items()}
    FX['USD'] = 1.0
    FXI = {}
    if ruta:
        with open(ruta, encoding='utf-8') as f:
            datos = json.load(f)
        for k, m in datos.items():
            try:
                v = float(m['valor'])
                if v > 0:
                    FX[k] = v
                    FXI[k] = m
            except Exception:
                pass
    return FX, FXI


fm = lambda n: f"{n:,.0f}".replace(',', '.')
f2 = lambda n: f"{n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
dd = lambda s: s[8:10] + '/' + s[5:7]
DM = lambda s: dd(s) + '/' + s[:4]


def fx_texto(monedas, FX, FXI, hoy):
    """Texto para el pie: cotización usada por moneda, con fuente y fecha, o aviso de respaldo."""
    out = []
    for c in sorted(monedas):
        if c == 'USD' or c not in FX:
            continue
        m = FXI.get(c)
        if not m:
            det = 'tipo fijo de referencia'
        elif m.get('respaldo'):
            det = f"respaldo del {DM(str(m.get('fecha') or hoy))}"
        else:
            det = f"{m.get('fuente') or 'sin fuente'} {DM(str(m.get('fecha') or hoy))}"
        out.append(f"{f2(FX[c])} {c} ({e(det)})")
    return '; '.join(out) or 'sin monedas locales'


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))


# --- Comparación con la corrida anterior -------------------------------------------------
# Cada dashboard embebe sus métricas en un bloque JSON dentro del HTML publicado.
# La corrida siguiente copia ese JSON a previo.json y el script muestra los cambios.

def bloque_metricas(m):
    """Bloque <script type="application/json" id="metricas"> para embeber en el HTML."""
    return '<script type="application/json" id="metricas">' + json.dumps(m, ensure_ascii=False) + '</script>'


def cargar_previo(ruta):
    """Lee previo.json; devuelve {} si no existe, está vacío o es inválido."""
    if not ruta:
        return {}
    try:
        with open(ruta, encoding='utf-8') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def texto_cambios(previo, actual, etiquetas):
    """'Desde el dd/mm/aaaa: abiertos 20 → 22 · con valor 0 → 5 …' (solo lo que cambió)."""
    if not previo or not previo.get('fecha'):
        return ''
    partes = []
    for clave, etiqueta in etiquetas:
        a, b = previo.get(clave), actual.get(clave)
        if a is None or b is None or a == b:
            continue
        partes.append(f'{etiqueta} {fm(a)} → <b>{fm(b)}</b>')
    desde = DM(str(previo['fecha']))
    if not partes:
        return f'Sin cambios en las cifras principales desde el {desde}.'
    return f'Cambios desde el {desde}: ' + ' · '.join(partes) + '.'
