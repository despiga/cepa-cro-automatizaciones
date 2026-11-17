# -*- coding: utf-8 -*-
"""Dashboard comercial de una base con un solo vendedor y leads etiquetados (p. ej. Región Norte).
Uso: python3 -I dashboard_vendedor.py config.json DEALS HECHAS PENDIENTES LEADS salida.html AAAA-MM-DD [fx.json] [previo.json]"""
import os,sys,collections,datetime as dt
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from html import escape as e
from common import cargar_config,cargar_lista,cargar_fx,fx_texto,fm,dd,DM,parse_ts as P,bloque_metricas,cargar_previo,texto_cambios
from estilos import css,cabecera
C=cargar_config(sys.argv[1])
deals,hechas,pend,leads=[cargar_lista(f) for f in sys.argv[2:6]]; OUT=sys.argv[6]
TODAY=sys.argv[7] if len(sys.argv)>7 else dt.date.today().isoformat()
FX,FXI=cargar_fx(sys.argv[8] if len(sys.argv)>8 else None,C['fx_respaldo'])
PREVIO=cargar_previo(sys.argv[9] if len(sys.argv)>9 else None)
Y=TODAY[:4]
usd=lambda x:(x['value'] or 0)/FX.get(x['currency'],1)
OWNER=int(C['owner_id']); PIPE=int(C['pipeline_id']); URL=C['pipedrive_url'].rstrip('/')
REC=C['etiqueta_recompra']; PRO=C['etiqueta_prospeccion']
ST=[tuple(x) for x in C['etapas']]
SI={s[0]:s for s in ST}
now=dt.datetime.fromisoformat(TODAY+'T12:00:00+00:00')
sc=lambda x:x['stage_change_time'] or x['add_time']
deals=[x for x in deals if x.get('pipeline_id')==PIPE and x.get('owner_id')==OWNER]
op=[x for x in deals if x['status']=='open' and x['stage_id'] in SI]
won=[x for x in deals if x['status']=='won']; lost=[x for x in deals if x['status']=='lost']
acts={a['id']:a for a in pend}
nop=len(op); conv=sum(1 for x in op if x['value'])
tusd=round(sum(usd(x) for x in op)); pond=round(sum(usd(x)*SI[x['stage_id']][2] for x in op))
# Embudo por etapa
cnt={s[0]:[x for x in op if x['stage_id']==s[0]] for s in ST}; maxn=max([len(v) for v in cnt.values()]+[1])
fun=''
for sid,n,p,rot in ST:
    ds=cnt[sid]; u=round(sum(usd(x) for x in ds)); cv=sum(1 for x in ds if x['value'])
    fun+=f'<div class="frow"><div class="flab"><b>{e(n)}</b><span>{int(p*100)}%</span></div><div class="fbar"><span class="seg" style="width:{len(ds)/maxn*100:.2f}%;background:var(--v1)" title="{e(n)}: {len(ds)}"></span></div><div class="fnum"><b>{len(ds)}</b><span>USD {fm(u)} · {cv} con valor</span></div></div>'
# Estancados (excluye cambios masivos de etapa)
cd=collections.Counter(sc(x)[:10] for x in op); bulk={d for d,c in cd.items() if c>=C.get('umbral_bloque',15)}
nbulk=sum(1 for x in op if sc(x)[:10] in bulk)
est=[]
for x in op:
    if sc(x)[:10] in bulk: continue
    d=(now-P(sc(x))).days; rot=SI[x['stage_id']][3]
    if d>rot: est.append((d,x))
est.sort(key=lambda t:-t[0])
# Tabla de abiertos
def prox(x):
    a=acts.get(x.get('next_activity_id'))
    if not a or not a.get('due_date'): return ('Sin actividad agendada','warn')
    s=DM(a['due_date']); return (s+(' · vencida' if a['due_date']<TODAY else ''),'warn' if a['due_date']<TODAY else '')
orden={s[0]:i for i,s in enumerate(ST)}
rows=''
for x in sorted(op,key=lambda x:(-orden[x['stage_id']],x['title'])):
    pr,cls=prox(x); val=f"{x['currency']} {fm(x['value'])}" if x['value'] else '<span class="mut">Sin valor</span>'
    rows+=f'<tr><td><a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a></td><td>{e(SI[x["stage_id"]][1])}</td><td class="num">{val}</td><td class="{cls}">{e(pr)}</td></tr>'
sin_act=sum(1 for x in op if prox(x)[0]=='Sin actividad agendada'); venc_act=sum(1 for x in op if 'vencida' in prox(x)[0])
# Ganados y perdidos
wy=[x for x in won if (x['won_time'] or '')[:4]==Y]; wy.sort(key=lambda x:x['won_time'],reverse=True)
wtot=round(sum(usd(x) for x in wy)); wval=sum(1 for x in wy if x['value'])
wrows=''.join(f'<tr><td>{dd(x["won_time"])}</td><td><a href="{URL}/deal/{x["id"]}">{e(x["title"])}</a></td><td class="num">{(x["currency"]+" "+fm(x["value"])) if x["value"] else "<span class=mut>Sin valor</span>"}</td><td class="num">{fm(usd(x))}</td></tr>' for x in wy[:20]) or '<tr><td colspan="4">Sin ganados este año.</td></tr>'
ly=[x for x in lost if (x['lost_time'] or '')[:4]==Y]; ly.sort(key=lambda x:x['lost_time'],reverse=True)
lostli=''.join(f'<li><b>{e(x["title"])}</b> · {dd(x["lost_time"])} · {e(x["lost_reason"] or "sin motivo")}</li>' for x in ly[:12]) or '<li>Ninguno en el pipeline.</li>'
# Leads
act_leads=[l for l in leads if not l.get('is_archived')]
rec=[l for l in act_leads if REC in (l.get('label_ids') or [])]; pro=[l for l in act_leads if PRO in (l.get('label_ids') or [])]
otros=len(act_leads)-len(rec)-len(pro)
def lstat(ls):
    sa=sum(1 for l in ls if not l.get('next_activity_id') or l['next_activity_id'] not in acts)
    ve=sum(1 for l in ls if l.get('next_activity_id') in acts and (acts[l['next_activity_id']].get('due_date') or '9')<TODAY)
    return sa,ve
rs,rv=lstat(rec); ps,pv=lstat(pro)
# Actividad
hy=[x for x in hechas if (x.get('due_date') or '')[:4]==Y and x.get('due_date')<=TODAY]
last=max((x['due_date'] for x in hechas if x.get('due_date') and x['due_date']<=TODAY),default='')
semana=sum(1 for x in hechas if x.get('due_date') and 0<=(now.date()-dt.date.fromisoformat(x['due_date'])).days<=7)
pv_=[x for x in pend if x.get('due_date') and x['due_date']<TODAY]
oldest=min((x['due_date'] for x in pend if x.get('due_date')),default='')
hm=collections.Counter(x['due_date'][:7] for x in hy)
mrows=''.join(f'<span class="chip">{m[5:]}/{m[2:4]} · {c}</span>' for m,c in sorted(hm.items())[-6:])
estli=''.join(f'<li><b>{e(x["title"])}</b> · {e(SI[x["stage_id"]][1])} · {d} días sin cambio (límite {SI[x["stage_id"]][3]})</li>' for d,x in est[:12])
if est: estxt=f'<b>Estancados:</b> {len(est)} negocios pasaron el límite de su etapa.<ul>{estli}</ul>'+(f'<small>Se excluyen {nbulk} negocios con carga masiva el {", ".join(DM(b) for b in sorted(bulk))}.</small>' if bulk else '')
else: estxt='<b>Estancados:</b> ninguno con dato confiable.'+(f' {nbulk} negocios se cargaron en bloque el {", ".join(DM(b) for b in sorted(bulk))}; el conteo real aparece cuando pasen los días de cada etapa (7 a 21).' if bulk else '')
fxfoot=fx_texto({x['currency'] for x in deals}|set(FXI),FX,FXI,TODAY)
CSS=css(960,'18px 20px',520,extra=(
    '.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}\n'
    '.kpi{background:var(--card);border:1px solid var(--line);padding:14px 16px}.kpi small{color:var(--mut);display:block}\n'
    '.kpi b{font:700 26px var(--hf);color:var(--navy);display:block;font-variant-numeric:tabular-nums}.kpi span{color:var(--mut);font-size:12px}\n'
    '.frow{display:grid;grid-template-columns:150px 1fr 170px;gap:12px;align-items:center;padding:7px 0;border-top:1px solid var(--line)}\n'
    '.flab span{color:var(--mut);margin-left:6px;font-size:12px}\n'
    '.fbar{display:flex;background:var(--trk);height:22px;min-width:0}.seg{display:block;height:100%}\n'
    '.fnum{text-align:right;font-variant-numeric:tabular-nums}.fnum span{display:block;color:var(--mut);font-size:12px}\n'
    '.lgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:10px}\n'
    '.lbox{border:1px solid var(--line);padding:12px 14px}.lbox b{font:700 22px var(--hf);color:var(--navy)}\n'
    '.chip{display:inline-block;border:1px solid var(--line);padding:2px 8px;margin:4px 6px 0 0;font-size:12px;color:var(--mut)}\n'
    '@media (max-width:520px){.frow{grid-template-columns:1fr;gap:4px}.fnum{text-align:left}}\n'))
METR={'fecha':TODAY,'abiertos':nop,'con_valor':conv,'usd':tusd,'ponderado':pond,'ganados_anio':len(wy),'usd_ganado':wtot,'sin_actividad':sin_act,'proxima_vencida':venc_act,'leads_recompra':len(rec),'leads_prospeccion':len(pro)}
cambios=texto_cambios(PREVIO,METR,[('abiertos','abiertos'),('con_valor','con valor'),('usd','pipeline USD'),('ponderado','ponderado USD'),('ganados_anio','ganados en el año'),('usd_ganado','USD ganado'),('sin_actividad','sin actividad agendada'),('proxima_vencida','con la próxima vencida'),('leads_recompra','leads Recompra'),('leads_prospeccion','leads Prospección')])
html=cabecera(C["titulo"])+f'''<style>{CSS}</style>{bloque_metricas(METR)}</head><body>
<div class="wrap">
<header><h1>{e(C["titulo"])}</h1><p class="sub">{e(C["subtitulo"])} · datos de Pipedrive al {DM(TODAY)}</p></header>
<div class="note"><b>Leer con cuidado.</b> Solo {conv} de {nop} negocios abiertos y {wval} de {len(wy)} ganados tienen valor cargado: los montos en dólares son un piso, no el total. Aún no hay metas cargadas, por eso no hay barras de cumplimiento.</div>
{f'<div class="delta">{cambios}</div>' if cambios else ''}
<section class="kpis">
<div class="kpi"><small>Pipeline abierto (USD)</small><b>{fm(tusd)}</b><span>solo negocios con valor ({conv} de {nop})</span></div>
<div class="kpi"><small>Ponderado por etapa (USD)</small><b>{fm(pond)}</b><span>valor × probabilidad de la etapa</span></div>
<div class="kpi"><small>Negocios abiertos</small><b>{nop}</b><span>{sin_act} sin actividad agendada · {venc_act} con la próxima vencida</span></div>
<div class="kpi"><small>Ganados en {Y} (USD)</small><b>{fm(wtot)}</b><span>{len(wy)} negocios · {wval} con valor</span></div>
</section>
<section class="card"><h2>Pipeline por etapa</h2><p class="sub">Negocios abiertos de {e(C["vendedor"])} en el {e(C["pipeline_texto"])}. A la derecha, el valor en USD de los que tienen valor.</p>
<div style="margin-top:10px">{fun}</div></section>
<section class="card"><h2>Negocios abiertos</h2><p class="sub">De la etapa más avanzada a la más temprana, con la próxima actividad agendada.</p><div class="tw"><table><thead><tr><th>Negocio</th><th>Etapa</th><th class="num">Valor</th><th>Próxima actividad</th></tr></thead><tbody>{rows or '<tr><td colspan="4">Sin negocios abiertos.</td></tr>'}</tbody></table></div></section>
<section class="card"><h2>Leads</h2><p class="sub">Cuentas a reactivar (Recompra) y prospectos sin calificar (Prospección).</p>
<div class="lgrid"><div class="lbox"><small>Recompra</small><br><b>{len(rec)}</b><br><small>{rs} sin actividad agendada · {rv} con actividad vencida</small></div>
<div class="lbox"><small>Prospección</small><br><b>{len(pro)}</b><br><small>{ps} sin actividad agendada · {pv} con actividad vencida</small></div></div>
{f'<p class="foot">Además hay {otros} leads antiguos sin etiqueta, fuera de este conteo.' + '</p>' if otros else ''}</section>
<section class="card"><h2>Ganados en {Y}</h2><div class="tw"><table><thead><tr><th>Fecha</th><th>Negocio</th><th class="num">Valor</th><th class="num">USD</th></tr></thead><tbody>{wrows}</tbody></table></div></section>
<section class="card"><h2>Perdidos en {Y}</h2><ul>{lostli}</ul></section>
<section class="card"><h2>Salud de la cartera</h2><ul>
<li><b>Sin valor:</b> {nop-conv} de {nop} abiertos y {len(wy)-wval} de {len(wy)} ganados.</li>
<li>{estxt}</li>
<li><b>Actividad registrada:</b> {len(hy)} actividades hechas en {Y}{f", la última el {DM(last)}" if last else ""}. Últimos 7 días: {semana}.<br>{mrows}</li>
<li><b>Pendientes vencidas:</b> {len(pv_)} de {len(pend)} pendientes; la más antigua es de {DM(oldest) if oldest else "—"}.</li></ul></section>
<p class="foot">Fuente: {e(C["fuente_texto"])}. Cotización por dólar: {fxfoot}. {e(C.get("fx_criterio",""))} Se actualiza solo cada lunes.</p>
</div></body></html>'''
open(OUT,'w',encoding='utf-8').write(html); print('ok',len(html),nop,conv,tusd,pond,len(wy),wtot,len(est),len(rec),len(pro))
