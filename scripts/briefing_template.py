# -*- coding: utf-8 -*-
"""Plantilla fija del briefing diario por mail. Uso: from briefing_template import render; html = render(d).
d: asunto, region, vendedor, fecha, agenda, fichas, calidad, pie, banner (opcional), leads (opcional), leads_vacio (opcional)."""
from html import escape as e
NAVY="#17324D"; INK="#1F2933"; MUTED="#5B6670"; LINE="#DDE3E8"; BG="#F3F5F7"; CARD="#FFFFFF"; ACCENT="#B4531A"; WARN_BG="#FDF1E7"; OK="#2F6F4F"
FONT="Arial,Helvetica,sans-serif"
def _h(t): return f'<div style="font:bold 13px {FONT};color:{NAVY};margin:18px 0 6px 0;padding-top:12px;border-top:1px solid {LINE}">{e(t)}</div>'
def _p(t): return f'<div style="font:14px/1.55 {FONT};color:{INK}">{t}</div>'
def _ul(items, empty="Sin datos registrados en Pipedrive."):
    if not items: return f'<div style="font:14px {FONT};color:{MUTED};font-style:italic">{e(empty)}</div>'
    return '<ul style="margin:0;padding-left:20px;font:14px/1.55 '+FONT+';color:'+INK+'">'+''.join(f'<li style="margin:0 0 5px 0">{i}</li>' for i in items)+'</ul>'
def _ficha(f):
    rows=''.join(f'<tr><td style="padding:3px 14px 3px 0;font:13px {FONT};color:{MUTED};white-space:nowrap;vertical-align:top">{e(k)}</td><td style="padding:3px 0;font:13px {FONT};color:{INK}">{v}</td></tr>' for k,v in f['datos'])
    tl=''.join(f'<tr><td style="padding:4px 12px 4px 0;font:13px {FONT};color:{MUTED};white-space:nowrap;vertical-align:top">{e(d)}</td><td style="padding:4px 0;font:13px/1.5 {FONT};color:{INK}">{t}</td></tr>' for d,t in f['linea']) or f'<tr><td style="font:italic 13px {FONT};color:{MUTED}">Sin interacciones registradas.</td></tr>'
    if f['alertas']:
        alert=f'<div style="background:{WARN_BG};border-left:3px solid {ACCENT};padding:10px 14px;margin:0">{_ul(f["alertas"])}</div>'
    else:
        alert=f'<div style="font:14px {FONT};color:{OK}">Sin alertas.</div>'
    return f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border:1px solid {LINE};margin:0 0 18px 0"><tr><td style="padding:20px 24px">
<div style="font:bold 17px {FONT};color:{NAVY}">{e(f["titulo"])}</div>
<div style="font:13px {FONT};color:{MUTED};margin:2px 0 10px 0">{e(f["subtitulo"])}</div>
<table role="presentation" cellpadding="0" cellspacing="0">{rows}</table>
{_h("Resumen ejecutivo")}{_p(f["resumen"])}
{_h("Línea de tiempo de interacciones")}<table role="presentation" cellpadding="0" cellspacing="0">{tl}</table>
{_h("Compromisos pendientes de nuestra parte")}{_ul(f["compromisos"], "Sin compromisos pendientes registrados.")}
{_h("Señales de alerta")}{alert}
{_h("Preguntas sugeridas para la conversación")}{_ul(f["preguntas"])}
</td></tr></table>'''
def _leads(leads, vacio):
    if not leads:
        body=f'<div style="font:14px {FONT};color:{MUTED};font-style:italic">{e(vacio)}</div>'
    else:
        n=len(leads); sv=sum(1 for l in leads if not l['visto']); sa=sum(1 for l in leads if not l['prox']); sval=sum(1 for l in leads if not l['valor'])
        resumen=f'<div style="font:13px {FONT};color:{MUTED};margin:0 0 8px 0">{n} leads · {sv} sin ver · {sa} sin próxima actividad · {sval} sin valor cargado</div>'
        rows=''.join(f'<tr><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{INK}"><a href="{e(l["url"])}" style="color:{NAVY};text-decoration:underline"><b>{e(l["titulo"])}</b></a><br><span style="color:{MUTED}">{e(l["origen"])}</span></td><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{INK}">{e(l["valor"] or "Sin valor cargado")}</td><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{MUTED};white-space:nowrap">{e(l["creado"])}</td><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{MUTED}">{e(l["prox"] or "Sin actividad")}</td></tr>' for l in leads)
        hdr=''.join(f'<td style="padding:4px 10px;font:bold 12px {FONT};color:{MUTED}">{h}</td>' for h in ["Lead","Valor","Creado","Próxima actividad"])
        body=resumen+f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{hdr}</tr>{rows}</table>'
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border:1px solid {LINE};margin:0 0 18px 0"><tr><td style="padding:18px 24px"><div style="font:bold 15px {FONT};color:{NAVY};margin-bottom:8px">Leads asignados ({len(leads or [])})</div>{body}</td></tr></table>'
def render(d):
    ag=''.join(f'<tr><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{MUTED};white-space:nowrap">{e(a["hora"])}</td><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{INK}"><a href="{e(a["url"])}" style="color:{NAVY};text-decoration:underline"><b>{e(a["actividad"])}</b></a><br><span style="color:{MUTED}">{e(a["cliente"])}</span></td><td style="padding:7px 10px;border-top:1px solid {LINE};font:13px {FONT};color:{MUTED}">{e(a["tipo"])}</td></tr>' for a in d['agenda'])
    banner=f'<div style="background:{ACCENT};color:#fff;font:bold 12px {FONT};padding:8px 24px;text-align:center">{e(d["banner"])}</div>' if d.get('banner') else ''
    fichas=''.join(_ficha(f) for f in d['fichas'])
    leads=_leads(d['leads'], d.get('leads_vacio','No tenés leads asignados en Pipedrive.')) if 'leads' in d else ''
    dq=''.join(f'<li style="margin:0 0 4px 0">{x}</li>' for x in d['calidad'])
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(d["asunto"])}</title></head>
<body style="margin:0;padding:0;background:{BG}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG}"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%">
<tr><td>{banner}<div style="background:{NAVY};padding:22px 24px"><div style="font:13px {FONT};color:#B9C7D6">Briefing diario · {e(d["region"])}</div><div style="font:bold 22px {FONT};color:#fff;margin-top:4px">{e(d["vendedor"])}</div><div style="font:14px {FONT};color:#DCE6EF;margin-top:2px">{e(d["fecha"])}</div></div></td></tr>
<tr><td style="padding:18px 0 0 0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border:1px solid {LINE};margin:0 0 18px 0"><tr><td style="padding:18px 24px 8px 24px"><div style="font:bold 15px {FONT};color:{NAVY}">Agenda del día ({len(d["agenda"])})</div></td></tr><tr><td style="padding:0 14px 14px 14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{ag}</table></td></tr></table>
{fichas}
{leads}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border:1px solid {LINE}"><tr><td style="padding:16px 24px"><div style="font:bold 13px {FONT};color:{NAVY};margin-bottom:6px">Calidad de datos de tu cartera</div><ul style="margin:0;padding-left:20px;font:13px/1.5 {FONT};color:{INK}">{dq}</ul></td></tr></table>
<div style="font:12px/1.5 {FONT};color:{MUTED};padding:14px 4px">{e(d["pie"])}</div>
</td></tr></table></td></tr></table></body></html>'''
