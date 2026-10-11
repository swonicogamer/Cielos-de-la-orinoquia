"""Noticias originales en español + recursos temáticos; sin generación de IA."""
import json, re, html, unicodedata, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = 'https://ciencia.nasa.gov/feed/'
OUT = Path(__file__).parent / 'boletin.json'
LESSONS = [
 ('exoplaneta', 'Exoplanetas', ['exoplanet','transito'], 'all-about-exoplanets', '¿Cómo detectarías un planeta que no puedes ver directamente?', 'Representen una estrella con una linterna y un planeta con una pelota. Observen la disminución de luz cuando la pelota cruza delante. No miren directamente una luz intensa.'),
 ('luna', 'La Luna', ['luna','artemis'], 'moon-phases', '¿Qué parte de la Luna está iluminada y qué parte podemos ver desde la Tierra?', 'Usen una pelota y una lámpara para representar las fases. La sombra de la Tierra no es la causa de las fases.'),
 ('galaxia', 'Galaxias', ['galax','via lactea'], 'galaxy', '¿Qué diferencia hay entre una estrella y una galaxia?', 'Dibujen una estrella, un sistema planetario y una galaxia. Expliquen qué contiene cada uno.'),
 ('nebulosa', 'Nebulosas', ['nebulosa'], 'nebula', '¿Qué preguntas harías sobre una nube de gas y polvo?', 'Comparen una fotografía astronómica con un dibujo de observación. Anoten qué pueden afirmar a partir de cada representación.'),
 ('gravedad', 'Gravedad', ['gravit','agujero negro'], 'what-is-gravity', '¿Cómo sabemos que existe algo si solo observamos sus efectos?', 'Escriban una observación, una interpretación y una duda de la noticia. Mantengan separadas las tres.'),
 ('sol', 'El Sol', ['solar','sol ','sol:', 'corona'], 'sun', '¿Qué diferencia hay entre observar el Sol y observar una estrella de noche?', 'Dibujen el Sol y escriban qué quieren aprender. No observen el Sol con el telescopio ni con binoculares sin equipo solar adecuado y supervisión.'),
]
def clean(s):
 s=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', s or '', flags=re.S|re.I)
 return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', s)).split())
def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def request(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CielosOrinoquia-Educacion/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r: return r.read()
def lesson(text):
 for _,topic,keys,slug,q,activity in LESSONS:
  if any(k in text for k in keys): return topic,slug,q,activity
 return 'Exploración espacial','spacecraft','¿Qué midieron los investigadores y qué interpretación proponen?','Identifiquen una evidencia, una explicación y algo que aún no se sabe. Escríbanlo en la bitácora.'
def build(raw, now):
 root=ET.fromstring(raw); articles=[]; seen=set()
 for item in root.findall('./channel/item'):
  title=clean(item.findtext('title')); url=item.findtext('link') or ''
  categories=' '.join(x.text or '' for x in item.findall('category'))
  text=norm(title+' '+categories)
  if not url.startswith('https://ciencia.nasa.gov/') or url in seen: continue
  if not any(k in text for k in ['universo','astronom','luna','artemis','planeta','saturno','jupiter','webb','hubble','galax','estrella','espacial','meteoro','cielo','solar']): continue
  try: date=parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc).date()
  except (TypeError,ValueError): continue
  if date>now.date() or (now.date()-date).days>45: continue
  description=clean(item.findtext('description')).split('The post ')[0].strip()
  if len(description)<30: description='Lee la explicación original en español de NASA. Esta tarjeta no incluye un resumen automático del descubrimiento.'
  words=description.split(); summary=' '.join(words[:55])+('…' if len(words)>55 else '')
  topic,slug,q,activity=lesson(text)
  articles.append(dict(title=title,url=url,date=date.isoformat(),summary=summary,source='NASA Ciencia · español',topic=topic,glyph='✦',meaning='Recurso educativo relacionado con el tema; no es una explicación específica de este descubrimiento.',question=q,activity=activity,educationUrl=f'https://spaceplace.nasa.gov/{slug}/sp/'))
  seen.add(url)
 articles.sort(key=lambda a:a['date'],reverse=True)
 if not articles: raise ValueError('No hay novedades pertinentes: conservar la última edición.')
 day=now.date().isoformat()
 return dict(schemaVersion=1,id='automatico',title='Noticias y recursos educativos · NASA',updated=day,reviewAfter=(now.date()+timedelta(days=8)).isoformat(),checkedAt=now.isoformat(),latestNewsDate=articles[0]['date'],articles=articles[:3],events=[],challengeTitle='De la noticia a la bitácora',challenge='Elige una noticia y registra qué observaron o midieron, qué explicación proponen y qué queda por investigar. Consulta el recurso educativo relacionado.')
def main():
 data=build(request(FEED),datetime.now(timezone.utc))
 temp=OUT.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(OUT)
 print(f"Boletín válido: {len(data['articles'])} noticias; fecha más reciente {data['latestNewsDate']}")
if __name__=='__main__': main()
