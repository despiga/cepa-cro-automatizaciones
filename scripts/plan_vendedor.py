# -*- coding: utf-8 -*-
"""Plan semanal de un vendedor (p. ej. Región Norte): actividades de lunes a viernes, negocios, leads y compromisos.
Uso: python3 -I plan_vendedor.py config.json DEALS PENDIENTES HECHAS LEADS ORGS salida.html AAAA-MM-DD"""
import os, sys, re, html as H, datetime as dt
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html import escape as e
from common import cargar_config, cargar_lista, fm
from estilos import css, cabecera

C = cargar_config(sys.argv[1])
deals, pend, hechas, leads, orgs = [cargar_lista(f) for f in sys.argv[2:7]]
OUT = sys.argv[7]
TODAY = dt.date.fromisoformat(sys.argv[8] if len(sys.argv) > 8 else dt.date.today().isoformat())
MON = TODAY - dt.timedelta(days=TODAY.weekday()); FRI = MON + dt.timedelta(days=4)
fmt = lambda d: d.strftime('%d/%m'); D = lambda s: dt.date.fromisoformat(s)
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
OWNER = int(C['owner_id']); PIPE = int(C['pipeline_id']); URL = C['pipedrive_url'].rstrip('/')
REC = C['etiqueta_recompra']; PRO = C['etiqueta_prospeccion']
VEND = C['vendedor']
ST = {int(x[0]): x[1] for x in C['etapas']}
TIPO = {'call': 'Llamada', 'meeting': 'Reunión', 'task': 'Tarea', 'deadline': 'Plazo', 'email': 'Mail', 'lunch': 'Almuerzo', 'envio_de_propuesta': 'Envío de propuesta', 'contacto_trunco': 'Contacto trunco', 'whats_app': 'WhatsApp', 'armado_propuesta': 'Armado de propuesta'}
ON = {o['id']: o['name'] for o in orgs}
deals = [x for x in deals if x.get('owner_id') == OWNER]
DI = {x['id']: x for x in deals}
op = [x for x in deals if x['status'] == 'open' and x.get('pipeline_id') == PIPE]
leads = [l for l in leads if not l.get('is_archived') and (REC in (l.get('label_ids') or []) or PRO in (l.get('label_ids') or []))]
LI = {l['id']: l for l in leads}
pend = [a for a in pend if a.get('owner_id', OWNER) == OWNER and a.get('due_date')]
AI = {a['id']: a for a in pend}


def ultima(n):
    if not n: return ''
    t = H.unescape(re.sub(r'<br\s*/?>|</div>|</p>|</li>', '\n', n)); t = re.sub(r'<[^>]+>', '', t).replace('\xa0', ' ')
    ls = [x.strip() for x in t.split('\n') if x.strip()]
    s = ls[-1] if ls else ''; return s if len(s) <= 160 else s[:157] + '…'


def ctx(a):
    if a.get('deal_id') and a['deal_id'] in DI:
        x = DI[a['deal_id']]; v = f"{x['currency']} {fm(x['value'])}" if x['value'] else 'sin valor'
        est = 'Ganado' if x['status'] == 'won' else ST.get(x['stage_id'], 'otro pipeline')
        return f'<a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a><br><small>{e(est)} · {e(v)}</small>'
    if a.get('lead_id') and a['lead_id'] in LI:
        l = LI[a['lead_id']]; tag = 'Recompra' if REC in (l.get('label_ids') or []) else 'Prospección'
        return f'<a href="{URL}/leads/inbox/{l["id"]}">{e(l["title"])}</a><br><small>Lead · {tag}</small>'
    return f'{e(ON.get(a.get("org_id"), "Sin organización"))}<br><small>Sin negocio ni lead</small>'


def fila(a, fecha=False):
    t = TIPO.get(a['type'], a['type']) + (' ' + a['due_time'][:5] if a.get('due_time') else '')
    u = ultima(a.get('note'))
    act = f'<b>{e(a["subject"])}</b>' + (f'<br><small>Última nota: {e(u)}</small>' if u else '')
    return '<tr>' + (f'<td>{fmt(D(a["due_date"]))}</td>' if fecha else '') + f'<td>{e(t)}</td><td>{act}</td><td>{ctx(a)}</td></tr>'


TH = '<th>Tipo</th><th>Actividad</th><th>Negocio / lead / cuenta</th>'
semana = [a for a in pend if MON <= D(a['due_date']) <= FRI]
vencidas = [a for a in pend if D(a['due_date']) < MON]
rec90 = [a for a in vencidas if (MON - D(a['due_date'])).days <= 90]; viejas = len(vencidas) - len(rec90)
prox = [a for a in pend if D(a['due_date']) > FRI]
next_of = lambda x: AI.get(x.get('next_activity_id'))
sin = [x for x in op if not next_of(x)]
venc_deal = [x for x in op if next_of(x) and D(next_of(x)['due_date']) < MON]
sinval = sum(1 for x in op if not x['value'])
lastw = MON - dt.timedelta(days=7)
gan = [x for x in deals if x['status'] == 'won' and x.get('won_time') and lastw <= D(x['won_time'][:10]) < MON]
per = [x for x in deals if x['status'] == 'lost' and x.get('lost_time') and lastw <= D(x['lost_time'][:10]) < MON and x.get('pipeline_id') == PIPE]
rec = [l for l in leads if REC in l['label_ids']]; pro = [l for l in leads if PRO in l['label_ids']]
lsin = [l for l in leads if l.get('next_activity_id') not in AI]
partes = [f'{VEND} tiene {len(semana)} actividades agendadas esta semana.']
if venc_deal: partes.append(f'{len(venc_deal)} de los {len(op)} negocios abiertos tienen la próxima actividad vencida.')
if sin: partes.append(f'{len(sin)} negocios abiertos no tienen ninguna actividad agendada.')
partes.append(f'{sinval} de {len(op)} abiertos siguen sin valor cargado.')
if gan or per: partes.append(f'La semana pasada: {len(gan)} ganados y {len(per)} perdidos.')
if lsin: partes.append(f'{len(lsin)} de {len(leads)} leads no tienen próxima actividad.')


def cuenta(ls):
    c = Counter(ST.get(x['stage_id'], '?') for x in ls); return ', '.join(f'{k}: {v}' for k, v in c.most_common())


cards = f'''<section class="team"><div class="pc"><h3>Negocios abiertos</h3><b class="big">{len(op)}</b> <small>en el {e(C["pipeline_texto"])}</small><p class="s">{len(venc_deal)} con la próxima actividad vencida{(' (' + cuenta(venc_deal) + ')') if venc_deal else ''} · {len(sin)} sin actividad agendada.</p>{('<p class="s">Primeros a reagendar: ' + '; '.join(e(x['title']) for x in venc_deal[:6]) + '.</p>') if venc_deal else ''}</div>
<div class="pc"><h3>Leads · Recompra</h3><b class="big">{len(rec)}</b> <small>cuentas a reactivar</small><p class="s">{sum(1 for l in rec if l.get('next_activity_id') not in AI)} sin próxima actividad.</p></div>
<div class="pc"><h3>Leads · Prospección</h3><b class="big">{len(pro)}</b> <small>prospectos</small><p class="s">{sum(1 for l in pro if l.get('next_activity_id') not in AI)} sin próxima actividad.</p></div></section>'''
dias = ''
for i in range(5):
    d = MON + dt.timedelta(days=i); acts = sorted([a for a in semana if D(a['due_date']) == d], key=lambda a: a.get('due_time') or '99')
    body = ''.join(fila(a) for a in acts) or '<tr><td colspan="3"><small>Sin actividades agendadas.</small></td></tr>'
    dias += f'<section class="card"><h2>{DIAS[i]} {fmt(d)} <small>· {len(acts)} actividades</small></h2><div class="tw"><table><thead><tr>{TH}</tr></thead><tbody>{body}</tbody></table></div></section>'


def lrow(l):
    a = AI.get(l.get('next_activity_id')); tag = 'Recompra' if REC in l['label_ids'] else 'Prospección'
    if a: pa = fmt(D(a['due_date'])) + (' · vencida' if D(a['due_date']) < MON else '') + f' · {e(a["subject"])}'
    else: pa = '<span class="warn">Sin actividad</span>'
    return f'<tr><td><a href="{URL}/leads/inbox/{l["id"]}">{e(l["title"])}</a></td><td>{tag}</td><td>{pa}</td><td>&nbsp;</td></tr>'


lrows = ''.join(lrow(l) for l in sorted(leads, key=lambda l: (0 if REC in l['label_ids'] else 1, l['title']))) or '<tr><td colspan="4"><small>Sin leads con etiqueta Recompra o Prospección.</small></td></tr>'
prows = ''.join(fila(a, True) for a in sorted(prox, key=lambda a: a['due_date'])[:25]) or '<tr><td colspan="4"><small>Nada agendado después del viernes.</small></td></tr>'
vrows = ''.join(fila(a, True) for a in sorted(rec90, key=lambda a: a['due_date'])) or '<tr><td colspan="4"><small>Sin vencidas en los últimos 90 días.</small></td></tr>'
gp = ''
if gan or per:
    gp = '<section class="card"><h2>Semana pasada</h2><ul>' + ''.join(f'<li>Ganado: <a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a> ({fmt(D(x["won_time"][:10]))})</li>' for x in gan) + ''.join(f'<li>Perdido: {e(x["title"])} ({fmt(D(x["lost_time"][:10]))}) · {e(x.get("lost_reason") or "sin motivo")}</li>' for x in per) + '</ul></section>'
comp = ''.join(f'<tr><td>{e(p)}</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' for p in C.get('filas_compromisos', [VEND] * 5))
CSS = css(1000, '16px 20px', 620, extra=(
    '.team{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.pc{background:var(--card);border:1px solid var(--line);padding:14px 16px}\n'
    '.big{font:700 28px var(--hf);color:var(--navy)}.s{font-size:13px;color:var(--mut);margin:6px 0 0}\n'))
TITULO = C.get('titulo_plan', C['titulo'])
rango = f'{MON.day} al {FRI.day} de {MESES[FRI.month-1]} de {FRI.year}' if MON.month == FRI.month else f'{MON.day} de {MESES[MON.month-1]} al {FRI.day} de {MESES[FRI.month-1]} de {FRI.year}'
out = cabecera(TITULO) + f'''
<style>{CSS}</style></head><body><div class="wrap">
<header><h1>{e(TITULO)}</h1><p class="sub">Semana del {rango} · para la reunión de seguimiento con {e(VEND)} del lunes {fmt(MON)} · datos de Pipedrive al {TODAY.strftime('%d/%m/%Y')}</p></header>
<div class="note"><b>Para decidir hoy.</b> {' '.join(partes)}</div>
{cards}
{gp}
{dias}
<section class="card"><h2>Leads de {e(VEND)}</h2><p class="sub">Primero Recompra (cuentas a reactivar), después Prospección. La última columna es para decidir en la reunión: convertir a negocio, seguir o archivar.</p><div class="tw"><table><thead><tr><th>Lead</th><th>Etiqueta</th><th>Próxima actividad</th><th>Decisión</th></tr></thead><tbody>{lrows}</tbody></table></div></section>
<section class="card"><h2>Próximas semanas <small>· ya agendado</small></h2><div class="tw"><table><thead><tr><th>Fecha</th>{TH}</tr></thead><tbody>{prows}</tbody></table></div>{f'<p class="foot">Se muestran las primeras 25 de {len(prox)}.</p>' if len(prox) > 25 else ''}</section>
<section class="card"><h2>Vencidas recientes a resolver <small>· últimos 90 días</small></h2><div class="tw"><table><thead><tr><th>Vencía</th>{TH}</tr></thead><tbody>{vrows}</tbody></table></div>{f'<p class="foot">Hay además {viejas} actividades pendientes vencidas hace más de 90 días que conviene cerrar en bloque.</p>' if viejas else ''}</section>
<section class="card"><h2>Compromisos de la semana <small>· completar en la reunión</small></h2><div class="tw"><table><thead><tr><th>Responsable</th><th>Compromiso</th><th>Negocio</th><th>Fecha</th></tr></thead><tbody>{comp}</tbody></table></div></section>
<p class="foot">{e(C.get("fuente_plan", C["fuente_texto"]))}</p>
</div></body></html>'''
open(OUT, 'w', encoding='utf-8').write(out)
print('ok', len(out), 'semana', len(semana), 'vencidas90', len(rec90), 'viejas', viejas, 'prox', len(prox), 'abiertos', len(op), 'leads', len(leads))
