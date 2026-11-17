# -*- coding: utf-8 -*-
"""Plan semanal de una base con varios vendedores (p. ej. Cono Sur) para la reunión de coordinación de los lunes.
Uso: python3 -I plan_equipo.py config.json ABIERTOS GANADOS PERDIDOS PENDIENTES LEADS salida.html AAAA-MM-DD [fx.json]
Usa los mismos datos que dashboard_equipo.py más los leads del responsable de leads.
Claves de config propias (además de las del dashboard): nombres_cortos {id: nombre de uso}, pipedrive_url,
responsable_leads (id, opcional), titulo_plan, subtitulo_plan, fuente_plan, filas_compromisos."""
import os, sys, re, html as H, datetime as dt
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html import escape as e
from common import cargar_config, cargar_lista, cargar_fx, fx_texto, fm
from estilos import css, cabecera

C = cargar_config(sys.argv[1])
op, won, lost, pend, leads = [cargar_lista(f) for f in sys.argv[2:7]]
OUT = sys.argv[7]
TODAY = dt.date.fromisoformat(sys.argv[8] if len(sys.argv) > 8 else dt.date.today().isoformat())
FX, FXI = cargar_fx(sys.argv[9] if len(sys.argv) > 9 else None, C['fx_respaldo'])
MON = TODAY - dt.timedelta(days=TODAY.weekday()); FRI = MON + dt.timedelta(days=4)
fmt = lambda d: d.strftime('%d/%m'); D = lambda s: dt.date.fromisoformat(s[:10])
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
URL = C['pipedrive_url'].rstrip('/')
CORTO = {int(k): v for k, v in C.get('nombres_cortos', C['vendedores']).items()}
EQ = list(CORTO)
RL = int(C['responsable_leads']) if C.get('responsable_leads') else None
ST = {int(x[0]): x[1] for x in C['etapas']}
TIPO = {'call': 'Llamada', 'meeting': 'Reunión', 'task': 'Tarea', 'deadline': 'Plazo', 'email': 'Mail', 'lunch': 'Almuerzo', 'envio_de_propuesta': 'Envío de propuesta', 'contacto_trunco': 'Contacto trunco', 'whats_app': 'WhatsApp', 'armado_propuesta': 'Armado de propuesta'}
dueno = lambda a: a.get('owner_id') or a.get('user_id')
quien = lambda i: CORTO.get(i, str(i))

op = [x for x in op if x.get('owner_id') in CORTO]
DI = {x['id']: x for x in op + won + lost}
pend = [a for a in pend if dueno(a) in CORTO and a.get('due_date') and not a.get('done')]
AI = {a['id']: a for a in pend}
leads = [l for l in leads if not l.get('is_archived') and (RL is None or l.get('owner_id', RL) == RL)]
LI = {l['id']: l for l in leads}


def valor(x):
    if not x.get('value'): return 'sin valor'
    t = f"{x['currency']} {fm(x['value'])}"
    if x['currency'] != 'USD' and x['currency'] in FX: t += f" (≈ USD {fm(x['value'] / FX[x['currency']])})"
    return t


def ultima(n):
    if not n: return ''
    t = H.unescape(re.sub(r'<br\s*/?>|</div>|</p>|</li>', '\n', n)); t = re.sub(r'<[^>]+>', '', t).replace('\xa0', ' ')
    ls = [x.strip() for x in t.split('\n') if x.strip()]
    s = ls[-1] if ls else ''; return s if len(s) <= 160 else s[:157] + '…'


def ctx(a):
    if a.get('deal_id') and a['deal_id'] in DI:
        x = DI[a['deal_id']]
        est = {'won': 'Ganado', 'lost': 'Perdido'}.get(x['status']) or ST.get(x['stage_id'], 'otro pipeline')
        return f'<a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a><br><small>{e(est)} · {e(valor(x))}</small>'
    if a.get('lead_id'):
        l = LI.get(a['lead_id']); t = l['title'] if l else 'Lead'
        return f'<a href="{URL}/leads/inbox/{a["lead_id"]}">{e(t)}</a><br><small>Lead</small>'
    if a.get('deal_id'):
        return f'<a href="{URL}/deal/{a["deal_id"]}">{e(a.get("deal_title") or "Negocio")}</a><br><small>fuera de los abiertos del filtro</small>'
    return f'{e(a.get("org_name") or "Sin negocio")}<br><small>Sin negocio ni lead</small>'


def fila(a, fecha=False):
    t = TIPO.get(a.get('type'), a.get('type') or 'Actividad') + (' ' + a['due_time'][:5] if a.get('due_time') else '')
    u = ultima(a.get('note'))
    act = f'<b>{e(a.get("subject") or "Sin asunto")}</b>' + (f'<br><small>{e(u)}</small>' if u else '')
    return '<tr>' + (f'<td>{fmt(D(a["due_date"]))}</td>' if fecha else '') + f'<td>{e(quien(dueno(a)))}</td><td>{e(t)}</td><td>{act}</td><td>{ctx(a)}</td></tr>'


TH = '<th>Responsable</th><th>Tipo</th><th>Actividad</th><th>Negocio</th>'
orden = lambda a: (a['due_date'], a.get('due_time') or '99', EQ.index(dueno(a)))
semana = sorted([a for a in pend if MON <= D(a['due_date']) <= FRI], key=orden)
vencidas = [a for a in pend if D(a['due_date']) < MON]
rec90 = sorted([a for a in vencidas if (MON - D(a['due_date'])).days <= 90], key=orden); viejas = len(vencidas) - len(rec90)
prox = sorted([a for a in pend if D(a['due_date']) > FRI], key=orden)
# Un negocio "tiene próxima actividad" si alguna pendiente (de hoy en adelante) apunta a él
futuras = {a.get('deal_id') for a in pend if a.get('deal_id') and D(a['due_date']) >= MON}
lastw = MON - dt.timedelta(days=7)
gan = [x for x in won if x.get('owner_id') in CORTO and x.get('won_time') and lastw <= D(x['won_time']) < MON]
per = [x for x in lost if x.get('owner_id') in CORTO and x.get('lost_time') and lastw <= D(x['lost_time']) < MON]

por = {}
for i in EQ:
    mine = [x for x in op if x['owner_id'] == i]
    sin = [x for x in mine if x['id'] not in futuras]
    sin.sort(key=lambda x: (-(x['value'] or 0) / FX.get(x['currency'], 1), x['title']))
    por[i] = dict(sem=sum(1 for a in semana if dueno(a) == i), ab=mine, sin=sin)
assert sum(len(p['ab']) for p in por.values()) == len(op)
assert sum(p['sem'] for p in por.values()) == len(semana)


def cuenta(ls):
    c = Counter(ST.get(x['stage_id'], 'otra etapa') for x in ls); return ', '.join(f'{k}: {v}' for k, v in c.most_common()) or 'ninguno'


lsin = [l for l in leads if l.get('next_activity_id') not in AI]
partes = [f'Hay {len(semana)} actividades agendadas esta semana: ' + ', '.join(f'{por[i]["sem"]} de {quien(i)}' for i in EQ[:-1]) + f' y {por[EQ[-1]]["sem"]} de {quien(EQ[-1])}.']
for i in EQ:
    p = por[i]
    if p['sin']: partes.append(f'{quien(i)} tiene {len(p["sin"])} de {len(p["ab"])} negocios abiertos sin actividad agendada.')
if gan or per: partes.append(f'La semana pasada: {len(gan)} ganados y {len(per)} perdidos.')
if RL is not None and lsin: partes.append(f'{len(lsin)} de {len(leads)} leads de {quien(RL)} no tienen próxima actividad.')
if rec90: partes.append(f'{len(rec90)} actividades vencidas en los últimos 90 días para resolver.')
if any(p['sin'] for p in por.values()): partes.append('La reunión es el momento de agendar los negocios sin actividad.')

cards = ''
for i in EQ:
    p = por[i]
    cards += (f'<div class="pc"><h3>{e(quien(i))}</h3><b class="big">{p["sem"]}</b> <small>actividades esta semana</small>'
              f'<p class="s">{len(p["ab"])} negocios abiertos · {len(p["sin"])} sin actividad agendada de acá en adelante ({e(cuenta(p["sin"]))}). Las vencidas no cuentan.</p>')
    if p['sin']: cards += '<p class="s">Primeros a agendar (mayor valor primero): ' + '; '.join(e(x['title']) for x in p['sin'][:6]) + '.</p>'
    if i == RL: cards += f'<p class="s">Leads: {len(leads)} asignados · {len(lsin)} sin próxima actividad.</p>'
    cards += '</div>'

dias = ''
for k in range(5):
    d = MON + dt.timedelta(days=k); acts = [a for a in semana if D(a['due_date']) == d]
    body = ''.join(fila(a) for a in acts) or '<tr><td colspan="4"><small>Sin actividades agendadas.</small></td></tr>'
    dias += f'<section class="card"><h2>{DIAS[k]} {fmt(d)} <small>· {len(acts)} actividades</small></h2><div class="tw"><table><thead><tr>{TH}</tr></thead><tbody>{body}</tbody></table></div></section>'


def lrow(l):
    a = AI.get(l.get('next_activity_id'))
    if a: pa = fmt(D(a['due_date'])) + (' · <span class="warn">vencida</span>' if D(a['due_date']) < TODAY else '') + f' · {e(a.get("subject") or "")}'
    else: pa = '<span class="warn">Sin actividad</span>'
    nuevo = l.get('add_time') and (TODAY - D(l['add_time'])).days <= 7
    estado = ('Nuevo' if nuevo else 'En calificación') + ('' if l.get('was_seen', True) else ' · sin ver')
    v = (l.get('value') or {}); val = f'<br><small>{e(v.get("currency", ""))} {fm(v["amount"])}</small>' if v.get('amount') else ''
    return f'<tr><td><a href="{URL}/leads/inbox/{l["id"]}">{e(l["title"])}</a>{val}</td><td>{estado}</td><td>{pa}</td><td>&nbsp;</td></tr>'


leadsec = ''
if RL is not None:
    lord = sorted(leads, key=lambda l: (0 if l.get('next_activity_id') in AI and D(AI[l['next_activity_id']]['due_date']) <= FRI else 1, -(D(l['add_time']).toordinal() if l.get('add_time') else 0)))
    lrows = ''.join(lrow(l) for l in lord[:30]) or f'<tr><td colspan="4"><small>No hay leads asignados a {e(quien(RL))} en Pipedrive (consulta del {TODAY.strftime("%d/%m/%Y")}).</small></td></tr>'
    leadsec = (f'<section class="card"><h2>Leads · {e(quien(RL))}</h2><p class="sub">Calificación: primero los que tienen actividad esta semana o vencida, después los más nuevos. '
               f'La última columna es para decidir en la reunión a quién se pasa cada lead calificado.</p><div class="tw"><table><thead><tr><th>Lead</th><th>Estado</th><th>Próxima actividad</th><th>Traspasar a</th></tr></thead><tbody>{lrows}</tbody></table></div>'
               + (f'<p class="foot">Se muestran 30 de {len(leads)}.</p>' if len(leads) > 30 else '') + '</section>')

prows = ''.join(fila(a, True) for a in prox[:25]) or '<tr><td colspan="5"><small>Nada agendado después del viernes.</small></td></tr>'
vrows = ''.join(fila(a, True) for a in rec90) or '<tr><td colspan="5"><small>Sin vencidas en los últimos 90 días.</small></td></tr>'
gp = ''
if gan or per:
    gp = ('<section class="card"><h2>Semana pasada</h2><ul>'
          + ''.join(f'<li>Ganado: <a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a> · {e(quien(x["owner_id"]))} · {e(valor(x))} ({fmt(D(x["won_time"]))})</li>' for x in gan)
          + ''.join(f'<li>Perdido: {e(x["title"])} · {e(quien(x["owner_id"]))} ({fmt(D(x["lost_time"]))}) · {e(x.get("lost_reason") or "sin motivo")}</li>' for x in per) + '</ul></section>')
filas = C.get('filas_compromisos') or [n for i in EQ for n in (quien(i), quien(i))]
comp = ''.join(f'<tr><td>{e(p)}</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' for p in filas)
monedas = {x['currency'] for x in op + gan if x.get('value')}
fxfoot = fx_texto(monedas, FX, FXI, TODAY.isoformat())
CSS = css(1000, '16px 20px', 620, extra=(
    '.team{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.pc{background:var(--card);border:1px solid var(--line);padding:14px 16px}\n'
    '.big{font:700 28px var(--hf);color:var(--navy)}.s{font-size:13px;color:var(--mut);margin:6px 0 0}.warn{color:var(--acc)}\n'))
TITULO = C.get('titulo_plan', C['titulo'])
rango = f'{MON.day} al {FRI.day} de {MESES[FRI.month-1]} de {FRI.year}' if MON.month == FRI.month else f'{MON.day} de {MESES[MON.month-1]} al {FRI.day} de {MESES[FRI.month-1]} de {FRI.year}'
sub = C.get('subtitulo_plan', 'para la reunión de coordinación del lunes')
out = cabecera(TITULO) + f'''
<style>{CSS}</style></head><body><div class="wrap">
<header><h1>{e(TITULO)}</h1><p class="sub">Semana del {rango} · {e(sub)} {fmt(MON)} · datos de Pipedrive al {TODAY.strftime('%d/%m/%Y')}</p></header>
<div class="note"><b>Para decidir hoy.</b> {e(' '.join(partes))}</div>
<section class="team">{cards}</section>
{gp}
{dias}
{leadsec}
<section class="card"><h2>Próximas semanas <small>· ya agendado</small></h2><div class="tw"><table><thead><tr><th>Fecha</th>{TH}</tr></thead><tbody>{prows}</tbody></table></div>{f'<p class="foot">Se muestran las primeras 25 de {len(prox)}.</p>' if len(prox) > 25 else ''}</section>
<section class="card"><h2>Vencidas recientes a resolver <small>· últimos 90 días</small></h2><div class="tw"><table><thead><tr><th>Vencía</th>{TH}</tr></thead><tbody>{vrows}</tbody></table></div>{f'<p class="foot">Hay además {viejas} actividades pendientes vencidas hace más de 90 días que conviene cerrar en bloque.</p>' if viejas else ''}</section>
<section class="card"><h2>Compromisos de la semana <small>· completar en la reunión</small></h2><div class="tw"><table><thead><tr><th>Responsable</th><th>Compromiso</th><th>Negocio</th><th>Fecha</th></tr></thead><tbody>{comp}</tbody></table></div></section>
<p class="foot">{e(C.get("fuente_plan", C["fuente_texto"]))} Valores en moneda original; ≈ USD con: {fxfoot}.</p>
</div></body></html>'''
open(OUT, 'w', encoding='utf-8').write(out)
print('ok', len(out), 'semana', len(semana), ' · '.join(f'{quien(i)} {por[i]["sem"]}' for i in EQ), 'abiertos', len(op),
      'sin_actividad', sum(len(p['sin']) for p in por.values()), 'ganados_sem', len(gan), 'perdidos_sem', len(per),
      'leads', len(leads), 'leads_sin_act', len(lsin), 'vencidas90', len(rec90), 'viejas', viejas, 'prox', len(prox))
