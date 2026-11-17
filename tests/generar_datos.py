# -*- coding: utf-8 -*-
"""Genera datos ficticios con la forma de las respuestas de Pipedrive, para probar los scripts sin tocar datos reales.
Uso: python3 -I tests/generar_datos.py carpeta_salida AAAA-MM-DD"""
import json, os, sys, datetime as dt
out, hoy = sys.argv[1], dt.date.fromisoformat(sys.argv[2])
os.makedirs(out, exist_ok=True)
d = lambda n: (hoy + dt.timedelta(days=n)).isoformat()
ts = lambda n: d(n) + 'T12:00:00Z'
REC, PRO = 'lbl-recompra', 'lbl-prospeccion'
def deal(i, owner, status='open', cur='UYU', val=1000, stage=124, **k):
    x = dict(id=i, title=f'Negocio {i}', status=status, currency=cur, value=val, stage_id=stage, owner_id=owner, pipeline_id=25,
             stage_change_time=ts(-30), add_time=ts(-60), won_time=None, lost_time=None, lost_reason=None, next_activity_id=None, org_id=1)
    x.update(k); return x
def act(i, owner, due, done=False, **k):
    x = dict(id=i, owner_id=owner, due_date=due, due_time='10:00', done=done, type='call', subject=f'Actividad {i}', note='<p>01/11 contacto</p><p>Última novedad</p>', deal_id=None, lead_id=None, org_id=1)
    x.update(k); return x
# Equipo (3 vendedores ficticios: 1, 2, 3)
op = [deal(1, 1, val=50000, next_activity_id=101), deal(2, 2, cur='ARS', val=9000000, stage=126), deal(3, 3, cur='USD', val=0, stage=125)]
won = [deal(4, 1, status='won', val=200000, won_time=ts(-10))]
lost = [deal(5, 2, status='lost', lost_time=ts(-5), lost_reason='Precio')]
acts = [act(101, 1, d(0), deal_id=1), act(102, 2, d(-20)), act(103, 3, d(10))]
hechas = [act(201, 1, d(-3), done=True)]
acts += [act(104, 3, d(-40), lead_id='LE1'), act(105, 2, d(-400))]
eq_leads = [dict(id='LE1', title='Lead del equipo', owner_id=3, is_archived=False, next_activity_id=104, was_seen=False, add_time=ts(-2), value=dict(amount=5000, currency='UYU')),
            dict(id='LE2', title='Lead archivado', owner_id=3, is_archived=True)]
for n, v in dict(eq_abiertos=op, eq_ganados=won, eq_perdidos=lost, eq_pend=acts, eq_hechas=hechas, eq_leads=eq_leads).items():
    json.dump({'data': v}, open(f'{out}/{n}.json', 'w'))
# Vendedor único (owner 9)
vd = [deal(11, 9, cur='COP', val=33000000, next_activity_id=301), deal(12, 9, cur='COP', val=0, stage=127),
      deal(13, 9, status='won', cur='PEN', val=10000, won_time=ts(-3)), deal(14, 9, status='lost', lost_time=ts(-2), lost_reason='Sin presupuesto')]
vp = [act(301, 9, d(1), deal_id=11), act(302, 9, d(-15), lead_id='L1'), act(303, 9, d(20)), act(304, 9, d(-200))]
vh = [act(401, 9, d(-1), done=True)]
vl = [dict(id='L1', title='Lead recompra', label_ids=[REC], next_activity_id=302, is_archived=False),
      dict(id='L2', title='Lead prospección', label_ids=[PRO], next_activity_id=None, is_archived=False),
      dict(id='L3', title='Lead viejo', label_ids=[], next_activity_id=None, is_archived=False)]
for n, v in dict(v_deals=vd, v_pend=vp, v_hechas=vh, v_leads=vl, v_orgs=[dict(id=1, name='Organización Ejemplo')]).items():
    json.dump(v, open(f'{out}/{n}.json', 'w'))
json.dump({'UYU': {'valor': 40.66, 'fecha': d(0), 'fuente': 'Google', 'respaldo': False},
           'ARS': {'valor': 1510, 'fecha': d(-3), 'fuente': 'respaldo fijo', 'respaldo': True},
           'COP': {'valor': 3301.43, 'fecha': d(0), 'fuente': 'Google', 'respaldo': False}}, open(f'{out}/fx.json', 'w'))
print('ok', out)
