#!/usr/bin/env bash
# Prueba de humo: genera datos ficticios, corre los reportes y la plantilla del briefing, y verifica la salida.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; HOY="${1:-$(date +%F)}"
python3 -I "$R/tests/generar_datos.py" "$T" "$HOY"
python3 -I "$R/scripts/dashboard_equipo.py" "$R/tests/config_equipo.json" $T/eq_abiertos.json $T/eq_ganados.json $T/eq_perdidos.json $T/eq_hechas.json $T/eq_pend.json $T/a.html "$HOY" $T/fx.json
python3 -I "$R/scripts/dashboard_equipo.py" "$R/tests/config_equipo.json" $T/eq_abiertos.json $T/eq_ganados.json $T/eq_perdidos.json $T/eq_hechas.json $T/eq_pend.json $T/a2.html "$HOY"
python3 -I "$R/scripts/plan_equipo.py" "$R/tests/config_equipo.json" $T/eq_abiertos.json $T/eq_ganados.json $T/eq_perdidos.json $T/eq_pend.json $T/eq_leads.json $T/e.html "$HOY" $T/fx.json
python3 -I "$R/scripts/dashboard_vendedor.py" "$R/tests/config_vendedor.json" $T/v_deals.json $T/v_hechas.json $T/v_pend.json $T/v_leads.json $T/b.html "$HOY" $T/fx.json
python3 -I "$R/scripts/plan_vendedor.py" "$R/tests/config_vendedor.json" $T/v_deals.json $T/v_pend.json $T/v_hechas.json $T/v_leads.json $T/v_orgs.json $T/c.html "$HOY"
python3 -I -c "import sys; sys.path.insert(0,'$R/scripts'); from briefing_template import render
d=dict(asunto='A',region='Región',vendedor='V',fecha='Hoy',agenda=[dict(hora='10:00',actividad='X',cliente='C',tipo='Llamada',url='u')],fichas=[dict(titulo='T',subtitulo='S',datos=[('Valor','1')],resumen='r',linea=[('01/01/2026','x')],compromisos=[],alertas=['a'],preguntas=['p'])],leads=[],leads_vacio='Sin leads.',calidad=['q'],pie='pie')
open('$T/d.html','w').write(render(d))"
# Comparación con la corrida anterior: se usa la salida de b.html como "publicada" y se cambian dos cifras
python3 -I "$R/scripts/extraer_metricas.py" $T/b.html $T/previo.json
python3 -I -c "import json;p='$T/previo.json';d=json.load(open(p));d['fecha']='2026-11-10';d['con_valor']=0;d['abiertos']=1;json.dump(d,open(p,'w'))"
python3 -I "$R/scripts/dashboard_vendedor.py" "$R/tests/config_vendedor.json" $T/v_deals.json $T/v_hechas.json $T/v_pend.json $T/v_leads.json $T/b2.html "$HOY" $T/fx.json $T/previo.json
grep -q "Cambios desde el 10/11/2026" $T/b2.html && echo "ok: comparación con corrida anterior"
for f in a a2 b b2 c d e; do python3 -I "$R/scripts/verificar.py" $T/$f.html; done
echo "TODO OK ($T)"
