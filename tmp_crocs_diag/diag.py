import json,re,requests
from bs4 import BeautifulSoup
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'})
urls=['https://www.crocs.fr/p/toy-story-buzz-leclair/10007229.html','https://www.crocs.eu/p/disney-and-pixar-toy-story-buzz-lightyear/10007229.html','https://www.crocs.com/p/classic-clog/10001.html']
out={}
for u in urls:
 try:
  r=S.get(u,timeout=25); txt=r.text
  hits=sorted(set(re.findall(r'https?[^"\'<> ]+',txt)))
  media=[x.replace('\\/','/') for x in hits if 'media.crocs.com' in x or 'Sites-masterCatalog' in x or '10007229' in x or '10001_' in x]
  scripts=[]
  soup=BeautifulSoup(txt,'html.parser')
  for sc in soup.find_all('script'):
   t=sc.string or sc.get_text() or ''
   if '10007229' in t or 'media.crocs.com' in t or '10001_' in t:
    scripts.append(t[:200000])
  out[u]={'status':r.status_code,'len':len(txt),'media':media[:500],'scripts':scripts[:20]}
 except Exception as e:out[u]={'error':repr(e)}
open('tmp_crocs_diag/diag.json','w').write(json.dumps(out,indent=2))
print(json.dumps({u:{'status':v.get('status'),'len':v.get('len'),'media':len(v.get('media',[])),'scripts':len(v.get('scripts',[]))} for u,v in out.items()},indent=2))
