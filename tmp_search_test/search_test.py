import json,re,html
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
queries=['Jungle Zebra Jibbitz Crocs','SS11 Seahorse Pink Lemonade Jibbitz','206633-100 Crocs','11016-4DM Crocs','Ariel Printed Rhinestone Jibbitz','ToGo Classic Mini Bag']
out={}
for q in queries:
 d={'duck':[],'google':[],'yandex':[]}
 try:
  t=S.get('https://duckduckgo.com/',params={'q':q},timeout=20).text
  m=re.search(r'vqd=["\']?([\d-]+)',t)
  if m:
   r=S.get('https://duckduckgo.com/i.js',params={'l':'wt-wt','o':'json','q':q,'vqd':m.group(1),'f':',,,','p':'1'},headers={'Referer':'https://duckduckgo.com/'},timeout=20)
   data=r.json(); d['duck']=[{'image':x.get('image'),'url':x.get('url'),'title':x.get('title'),'width':x.get('width'),'height':x.get('height')} for x in data.get('results',[])[:10]]
 except Exception as e:d['duck_error']=repr(e)
 try:
  t=S.get('https://www.google.com/search',params={'tbm':'isch','q':q,'hl':'en'},timeout=20).text
  pats=re.findall(r'\["(https?://[^"\\]+?(?:jpg|jpeg|png|webp)(?:\?[^"\\]*)?)",(\d+),(\d+)\]',t,re.I)
  seen=set()
  for u,w,h in pats:
   u=html.unescape(u)
   if u not in seen:d['google'].append({'image':u,'width':w,'height':h});seen.add(u)
   if len(d['google'])>=15:break
 except Exception as e:d['google_error']=repr(e)
 try:
  t=S.get('https://yandex.com/images/search',params={'text':q},timeout=20).text
  us=re.findall(r'"origUrl":"(.*?)"',t)
  for u in us[:15]: d['yandex'].append({'image':bytes(u,'utf-8').decode('unicode_escape').replace('\\/','/')})
 except Exception as e:d['yandex_error']=repr(e)
 out[q]=d
 print(q,len(d['duck']),len(d['google']),len(d['yandex']))
open('tmp_search_test/results.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
