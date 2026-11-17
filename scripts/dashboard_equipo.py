# -*- coding: utf-8 -*-
"""Dashboard comercial de una base con varios vendedores (p. ej. Cono Sur).
Uso: python3 -I dashboard_equipo.py config.json ABIERTOS GANADOS PERDIDOS HECHAS PENDIENTES salida.html AAAA-MM-DD [fx.json] [previo.json]
Cada argumento de datos es una ruta o varias separadas por coma (páginas de Pipedrive)."""
import os, sys, collections, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html import escape as e
from common import cargar_config, cargar_lista, cargar_fx, fx_texto, fm, dd, DM, parse_ts as P, bloque_metricas, cargar_previo, texto_cambios
from estilos import css, cabecera

C = cargar_config(sys.argv[1])
op, won, lost, hechas, pend = [cargar_lista(f) for f in sys.argv[2:7]]
OUT = sys.argv[7]
TODAY = sys.argv[8] if len(sys.argv) > 8 else dt.date.today().isoformat()
FX, FXI = cargar_fx(sys.argv[9] if len(sys.argv) > 9 else None, C['fx_respaldo'])
PREVIO = cargar_previo(sys.argv[10] if len(sys.argv) > 10 else None)
Y = TODAY[:4]
usd = lambda x: (x['value'] or 0) / FX.get(x['currency'], 1)
NAMES = {int(k): v for k, v in C['vendedores'].items()}; V = list(NAMES.values())
ST = [tuple(s) for s in C['etapas']]  # [id, nombre, probabilidad, días límite]
SI = {s[0]: s for s in ST}
PAL = ['var(--v1)', 'var(--v2)', 'var(--v3)', 'var(--v4)', 'var(--v5)']
VC = {v: PAL[i % len(PAL)] for i, v in enumerate(V)}
now = dt.datetime.fromisoformat(TODAY + 'T12:00:00+00:00')
sc = lambda x: x['stage_change_time'] or x['add_time']
ow = lambda x: NAMES.get(x['owner_id'], str(x['owner_id']))
UMBRAL = C.get('umbral_bloque', 20)

rows = []
for sid, n, p, rot in ST:
    r = {'etapa': n, 'prob': p}
    for v in V:
        ds = [x for x in op if x['stage_id'] == sid and ow(x) == v]
        r[v] = {'n': len(ds), 'usd': round(sum(usd(x) for x in ds))}
    rows.append(r)
nop = len(op); conv = sum(1 for x in op if x['value'])
tusd = round(sum(usd(x) for x in op)); pond = round(sum(usd(x) * SI[x['stage_id']][2] for x in op if x['stage_id'] in SI))
maxn = max(sum(r[v]['n'] for v in V) for r in rows) or 1
pv = {}
for v in V:
    mine = [x for x in op if ow(x) == v]
    pv[v] = (len(mine), sum(1 for x in mine if x['value']), round(sum(usd(x) for x in mine)), sum(usd(x) * SI[x['stage_id']][2] for x in mine if x['stage_id'] in SI))
fun = ''
for r in rows:
    tot = sum(r[v]['n'] for v in V); u = sum(r[v]['usd'] for v in V)
    segs = ''.join(f'<span class="seg" style="width:{r[v]["n"]/maxn*100:.2f}%;background:{VC[v]}" title="{e(v)}: {r[v]["n"]}"></span>' for v in V if r[v]['n'])
    fun += f'<div class="frow"><div class="flab"><b>{e(r["etapa"])}</b><span>{int(r["prob"]*100)}%</span></div><div class="fbar">{segs}</div><div class="fnum"><b>{tot}</b><span>USD {fm(u)}</span></div></div>'
legend = ''.join(f'<span class="lg"><i style="background:{VC[v]}"></i>{e(v)}</span>' for v in V)
vt = ''
for v in V:
    n, c, u, pw = pv[v]; sin = n - c; pct = (sin / n * 100) if n else 0
    vt += f'<tr><td>{e(v)}</td><td class="num">{n}</td><td class="num">{c}</td><td class="num">{fm(u)}</td><td class="num">{fm(pw)}</td><td><div class="mini"><span style="width:{pct:.0f}%"></span></div><small>{sin} de {n} sin valor ({pct:.0f}%)</small></td></tr>'
cd = collections.Counter(sc(x)[:10] for x in op); bulk = {d for d, c in cd.items() if c >= UMBRAL}
nbulk = sum(1 for x in op if sc(x)[:10] in bulk)
est = []
for x in op:
    if sc(x)[:10] in bulk or x['stage_id'] not in SI: continue
    d = (now - P(sc(x))).days; rot = SI[x['stage_id']][3]
    if d > rot: est.append((d, x))
est.sort(key=lambda t: -t[0])
estli = ''.join(f'<li><b>{e(x["title"])}</b> · {e(ow(x))} · {e(SI[x["stage_id"]][1])} · {d} días sin cambio (límite {SI[x["stage_id"]][3]})</li>' for d, x in est[:12])
if est: estxt = f'<b>Estancados:</b> {len(est)} negocios pasaron el límite de su etapa.<ul>{estli}</ul>' + (f'<small>Se excluyen {nbulk} negocios con cambio de etapa masivo el {", ".join(DM(b) for b in sorted(bulk))}.</small>' if bulk else '')
else: estxt = '<b>Estancados:</b> ninguno con dato confiable.' + (f' {nbulk} negocios tienen cambio de etapa masivo el {", ".join(DM(b) for b in sorted(bulk))}; el conteo real aparece cuando pasen los días de cada etapa.' if bulk else '')
wy = [x for x in won if (x['won_time'] or '')[:4] == Y]; wy.sort(key=lambda x: x['won_time'], reverse=True)
wtot = round(sum(usd(x) for x in wy))
wrows = ''.join(f'<tr><td>{dd(x["won_time"])}</td><td>{e(x["title"])}</td><td>{e(ow(x))}</td><td class="num">{x["currency"]} {fm(x["value"] or 0)}</td><td class="num">{fm(usd(x))}</td></tr>' for x in wy[:15]) or '<tr><td colspan="5">Sin ganados este año.</td></tr>'
wd = collections.Counter(x['won_time'][:10] for x in wy); topd, topn = (wd.most_common(1)[0] if wd else ('', 0))
big = max(wy, key=usd) if wy else None
wnote = ''
if wy and topn >= 3: wnote = f'{topn} de {len(wy)} se registraron como ganados el {dd(topd)}.' + (f' {e(big["title"])} pesa el {usd(big)/wtot*100:.0f}% del total.' if wtot else '') + ' Conviene confirmar si son cierres nuevos o un registro atrasado.'
ld = collections.Counter(x['lost_time'][:10] for x in lost if x['lost_time']); bd, bn = (ld.most_common(1)[0] if ld else ('', 0))
bulkl = bn >= UMBRAL
rec = [x for x in lost if x['lost_time'] and (not bulkl or x['lost_time'][:10] != bd) and x['lost_time'][:4] == Y]; rec.sort(key=lambda x: x['lost_time'], reverse=True)
lostli = ''.join(f'<li><b>{e(x["title"])}</b> · {dd(x["lost_time"])} · {e(x["lost_reason"] or "sin motivo")} · {e(ow(x))}</li>' for x in rec[:12]) or '<li>Ninguno.</li>'
ltxt = (f'{bn} de las {len(lost)} más recientes se cerraron en bloque el {dd(bd)} por inactividad. No cuentan como pérdida comercial. Desde entonces:' if bulkl else f'Perdidos de {Y} entre los {len(lost)} más recientes:')
# Detalle por moneda local (config: monedas_detalle = [[código, nombre en plural], ...])
nota_mon = ''; salud_mon = ''
for cod, nom in C.get('monedas_detalle', []):
    xs = [x for x in op if x['currency'] == cod]
    if not xs: continue
    cv = sum(1 for x in xs if x['value'])
    nota_mon += f'Los {len(xs)} negocios en {nom.lower()} tienen {cv} con valor. '
    salud_mon += f' {nom}: {len(xs)} negocios, {cv} con monto, por {cod} {fm(sum(x["value"] or 0 for x in xs))} (USD {fm(sum(usd(x) for x in xs))}).'
hy = [x for x in hechas if (x['due_date'] or '')[:4] == Y]
last = max((x['due_date'] for x in hechas if x['due_date'] and x['due_date'] <= TODAY), default='')
pv_ = [x for x in pend if x['due_date'] and x['due_date'] < TODAY]
oldest = min((x['due_date'] for x in pend if x['due_date']), default='')
pmore = ' (primera página del filtro, puede haber más)' if len(pend) >= 500 else ''
hechtxt = f'{len(hy)} actividades hechas en {Y}' + (f', la última el {DM(last)}' if last else '') + '. ' + ('Muy poco registro: no se puede medir ritmo comercial semanal.' if len(hy) < 40 else 'Ver ritmo mensual en Pipedrive.')
semana = sum(1 for x in hechas if x['due_date'] and (now.date() - dt.date.fromisoformat(x['due_date'])).days <= 7 and x['due_date'] <= TODAY)
fxfoot = fx_texto({x['currency'] for x in op + won + lost} | set(FXI), FX, FXI, TODAY)
CSS = css(960, '18px 20px', 520, extra=(
    '.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}\n'
    '.kpi{background:var(--card);border:1px solid var(--line);padding:14px 16px}.kpi small{color:var(--mut);display:block}\n'
    '.kpi b{font:700 26px var(--hf);color:var(--navy);display:block;font-variant-numeric:tabular-nums}.kpi span{color:var(--mut);font-size:12px}\n'
    '.frow{display:grid;grid-template-columns:150px 1fr 110px;gap:12px;align-items:center;padding:7px 0;border-top:1px solid var(--line)}\n'
    '.flab span{color:var(--mut);margin-left:6px;font-size:12px}\n'
    '.fbar{display:flex;background:var(--trk);height:22px;min-width:0}.seg{display:block;height:100%}\n'
    '.fnum{text-align:right;font-variant-numeric:tabular-nums}.fnum span{display:block;color:var(--mut);font-size:12px}\n'
    '.legend{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 0;color:var(--mut);font-size:13px}\n'
    '.lg i{display:inline-block;width:10px;height:10px;margin-right:6px}\n'
    '.mini{background:var(--trk);height:8px;width:140px}.mini span{display:block;height:100%;background:var(--acc)}\n'
    '@media (max-width:520px){.frow{grid-template-columns:1fr;gap:4px}.fnum{text-align:left}}\n'))
METR = {'fecha': TODAY, 'abiertos': nop, 'con_valor': conv, 'usd': tusd, 'ponderado': pond, 'ganados_anio': len(wy), 'usd_ganado': wtot, 'estancados': len(est)}
cambios = texto_cambios(PREVIO, METR, [('abiertos', 'abiertos'), ('con_valor', 'con valor'), ('usd', 'pipeline USD'), ('ponderado', 'ponderado USD'), ('ganados_anio', 'ganados en el año'), ('usd_ganado', 'USD ganado'), ('estancados', 'estancados')])
html = cabecera(C["titulo"]) + f'''<style>{CSS}</style>{bloque_metricas(METR)}</head><body>
<div class="wrap">
<header><h1>{e(C["titulo"])}</h1><p class="sub">{e(C["subtitulo"])} · {e(", ".join(V))} · datos de Pipedrive al {DM(TODAY)}</p></header>
<div class="note"><b>Leer con cuidado.</b> Solo {conv} de {nop} negocios abiertos tienen valor cargado, así que el pipeline en dólares es un piso, no el total. {nota_mon}Aún no hay metas cargadas, por eso no hay barras de cumplimiento.</div>
{f'<div class="delta">{cambios}</div>' if cambios else ''}
<section class="kpis">
<div class="kpi"><small>Pipeline abierto (USD)</small><b>{fm(tusd)}</b><span>solo negocios con valor ({conv} de {nop})</span></div>
<div class="kpi"><small>Ponderado por etapa (USD)</small><b>{fm(pond)}</b><span>valor × probabilidad de la etapa</span></div>
<div class="kpi"><small>Negocios abiertos</small><b>{nop}</b><span>{e(C["pipeline_texto"])}, {len(V)} vendedores</span></div>
<div class="kpi"><small>Ganados en {Y} (USD)</small><b>{fm(wtot)}</b><span>{len(wy)} negocios</span></div>
</section>
<section class="card"><h2>Pipeline por etapa</h2><p class="sub">Cantidad de negocios por etapa del {e(C["pipeline_texto"])}, abierta por vendedor. A la derecha, el valor en USD de los que tienen valor.</p>
<div style="margin-top:10px">{fun}</div><div class="legend">{legend}</div></section>
<section class="card"><h2>Por vendedor</h2><div class="tw"><table><thead><tr><th>Vendedor</th><th class="num">Abiertos</th><th class="num">Con valor</th><th class="num">USD</th><th class="num">Ponderado</th><th>Sin valor</th></tr></thead><tbody>{vt}</tbody></table></div></section>
<section class="card"><h2>Ganados en {Y}</h2><div class="tw"><table><thead><tr><th>Fecha</th><th>Negocio</th><th>Vendedor</th><th class="num">Valor</th><th class="num">USD</th></tr></thead><tbody>{wrows}</tbody></table></div>{f'<p class="foot">{wnote}</p>' if wnote else ''}</section>
<section class="card"><h2>Perdidos</h2><p class="sub">{ltxt}</p><ul>{lostli}</ul></section>
<section class="card"><h2>Salud de la cartera</h2><ul>
<li><b>Sin valor:</b> {nop-conv} de {nop} abiertos.{salud_mon}</li>
<li>{estxt}</li>
<li><b>Actividad registrada:</b> {hechtxt} Últimos 7 días: {semana}.</li>
<li><b>Pendientes vencidas:</b> {len(pv_)}{pmore}; la más antigua es de {DM(oldest) if oldest else "—"}. Conviene cerrarlas en bloque para que la métrica sirva.</li></ul></section>
<p class="foot">Fuente: {e(C["fuente_texto"])}. Cotización por dólar: {fxfoot}. {e(C.get("fx_criterio", ""))} Se actualiza solo cada lunes.</p>
</div></body></html>'''
open(OUT, 'w', encoding='utf-8').write(html)
print('ok', len(html), 'abiertos', nop, 'con_valor', conv, 'usd', tusd, 'ponderado', pond, 'ganados', len(wy), wtot, 'estancados', len(est))
