# -*- coding: utf-8 -*-
"""Extrae el bloque de métricas de un HTML publicado y lo guarda como previo.json ({} si no hay).
Uso: python3 -I extraer_metricas.py publicado.html previo.json"""
import json, re, sys
try:
    t = open(sys.argv[1], encoding='utf-8').read()
    m = re.search(r'<script type="application/json" id="metricas">(.*?)</script>', t, re.S)
    d = json.loads(m.group(1)) if m else {}
except Exception:
    d = {}
json.dump(d, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print('previo:', d.get('fecha', 'sin datos'))
