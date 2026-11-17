# -*- coding: utf-8 -*-
"""Control de calidad de un HTML generado: falla si aparece None, NaN o undefined como palabra suelta.
Uso: python3 -I verificar.py salida.html"""
import re, sys
t = open(sys.argv[1], encoding='utf-8').read()
txt = re.sub(r'<style.*?</style>', '', t, flags=re.S)
mal = sorted(set(re.findall(r'\b(None|NaN|nan|undefined|null)\b', re.sub(r'<[^>]+>', ' ', txt))))
if mal:
    print('ERROR: aparecen valores vacíos:', ', '.join(mal)); sys.exit(1)
print('ok: sin None/NaN/undefined')
