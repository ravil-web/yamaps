#!/usr/bin/env python3
from __future__ import annotations
import csv, html, io, json, os, re, time, unicodedata
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'better_outputs'; OUT.mkdir(parents=True,exist_ok=True)
SHARD=int(os.environ.get('SHARD','0')); SHARDS=int(os.environ.get('SHARDS','1'))
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
S=requests.Session(); S.headers.update({'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9,ru;q=0.8'})
STOP=set('crocs jibbitz charm charms shoe shoes adult adults for the and card style bag silicone togo momentwear classic unisex women men kids kid для взрослых обувь цвет размер модель момент сабо шлепанцы полуботинки'.split())
OVERRIDES={
'10001798':('https://www.tradeinn.com/f/7/79994/jibbitz-adult-kangaroo.webp','https://www.tradeinn.com/'),
'10001788':('https://www.superjeans.cz/7653-large_default/7653-obrazek-7653.jpg','https://www.superjeans.cz/'),
'11016-485':('https://d25-a.sdn.cz/d_25/d_15050805/img/32/1000x424_Opobbe.jpg?fl=res%2C350%2C350%2C1%2Cfff%7Cwebp%2C80','https://www.zbozi.cz/'),
'206633-100':('https://i5.walmartimages.com/seo/Crocs-Unisex-Baya-Lined-Fuzz-Strap-Clogs_d6273b96-7ace-47ca-a82b-353816091cf3.3e0e0ef4701a11090b952dc36750879c.jpeg?odnBg=FFFFFF&odnHeight=573&odnWidth=573','https://www.walmart.com/'),
'10000441':('https://f.fcdn.app/imgs/943cde/www.crocs.com.uy/crocuy/194c/webp/catalogo/CR10006840_1002_1/1024-1024/jibbitz-charm-tigger-face-multicolor.jpg','https://www.crocs.com.uy/'),
}
COLOR_MAP={'белый':'white','черный':'black','чёрный':'black','голубой':'blue','синий':'blue','зеленый':'green','зелёный':'green','желтый':'yellow','жёлтый':'yellow','розовый':'pink','серый':'grey','коричневый':'brown','красный':'red','оранжевый':'orange','фиолетовый':'purple','бежевый':'beige','хаки':'khaki','лавандовый':'lavender'}
TRANS=str.maketrans({'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'})

def fold(v):
 s=unicodedata.normalize('NFKD',str(v or '')).lower().translate(TRANS)
 s=''.join(c for c in s if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+',' ',s).strip()
def compact(v): return re.sub(r'[^a-z0-9]','',fold(v))
def terms(v): return [x for x in fold(v).split() if len(x)>=3 and x not in STOP]
def load_records():
 data=json.loads((ROOT/'records.json').read_text(encoding='utf-8'))
 return [r for i,r in enumerate(data) if i%SHARDS==SHARD]
def get(url,params=None,timeout=18,headers=None):
 try:
  r=S.get(url,params=params,timeout=timeout,allow_redirects=True,headers=headers or {})
  return r if r.status_code<400 else None
 except Exception:return None

def validate(url,ref=''):
 if not url or not url.startswith(('http://','https://')): return None
 if any(x in url.lower() for x in ('logo','placeholder','no-image','favicon','sprite','avatar','loading')): return None
 h={'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'}
 if ref:h['Referer']=ref
 r=get(url,timeout=20,headers=h)
 if not r:return None
 ct=(r.headers.get('content-type') or '').split(';')[0].lower()
 if not ct.startswith('image/') or len(r.content)<2500:return None
 w=hgt=0
 if ct!='image/svg+xml':
  try:
   im=Image.open(io.BytesIO(r.content));w,hgt=im.size
   if w<220 or hgt<220 or max(w/hgt,hgt/w)>7:return None
  except Exception:return None
 return {'image_url':r.url,'content_type':ct,'width':w,'height':hgt,'bytes':len(r.content)}

def ddg_images(q):
 out=[];r=get('https://duckduckgo.com/',params={'q':q})
 if not r:return out
 token=None
 for p in (r'vqd=["\']?([\d-]+)',r'vqd="([^"]+)"',r"vqd='([^']+)'"):
  m=re.search(p,r.text)
  if m:token=m.group(1);break
 if not token:return out
 r=get('https://duckduckgo.com/i.js',params={'l':'wt-wt','o':'json','q':q,'vqd':token,'f':',,,','p':'1'},headers={'Referer':'https://duckduckgo.com/'})
 if not r:return out
 try:data=r.json()
 except Exception:return out
 for x in data.get('results',[])[:18]:
  if x.get('image'):out.append({'image':x.get('image'),'page':x.get('url',''),'title':x.get('title',''),'engine':'duckduckgo'})
 return out

def google_images(q):
 out=[];r=get('https://www.google.com/search',params={'tbm':'isch','q':q,'hl':'en','safe':'active'})
 if not r:return out
 pats=re.findall(r'\["(https?://[^"\\]+?(?:jpg|jpeg|png|webp)(?:\?[^"\\]*)?)",(\d+),(\d+)\]',r.text,re.I);seen=set()
 for u,w,h in pats:
  u=html.unescape(u).replace('\\u003d','=').replace('\\u0026','&').replace('\\/','/')
  if u not in seen:out.append({'image':u,'page':'','title':'','engine':'google'});seen.add(u)
  if len(out)>=18:break
 return out

def yandex_images(q):
 out=[];r=get('https://yandex.com/images/search',params={'text':q,'isize':'large'})
 if not r:return out
 for m in re.finditer(r'"origUrl":"(.*?)"',r.text):
  u=m.group(1).encode().decode('unicode_escape').replace('\\/','/');context=r.text[max(0,m.start()-1500):min(len(r.text),m.end()+1500)]
  tm=re.search(r'"title":"(.*?)"',context);pm=re.search(r'"fromPageUrl":"(.*?)"',context)
  out.append({'image':u,'page':(pm.group(1).encode().decode('unicode_escape').replace('\\/','/') if pm else ''),'title':(tm.group(1).encode().decode('unicode_escape') if tm else ''),'engine':'yandex'})
  if len(out)>=18:break
 return out

def page_images(url):
 r=get(url,timeout=18)
 if not r or 'html' not in (r.headers.get('content-type') or '').lower():return {},[]
 soup=BeautifulSoup(r.text,'html.parser');text=soup.get_text(' ',strip=True)[:150000]
 meta={'url':r.url,'title':soup.title.get_text(' ',strip=True) if soup.title else '','text':text,'sku':'','name':''};imgs=[]
 for prop in ('og:image','og:image:secure_url','twitter:image','twitter:image:src'):
  for t in soup.find_all('meta',attrs={'property':prop})+soup.find_all('meta',attrs={'name':prop}):
   if t.get('content'):imgs.append(urljoin(r.url,t['content']))
 for sc in soup.find_all('script',attrs={'type':re.compile(r'ld\+json',re.I)}):
  try:d=json.loads(sc.string or sc.get_text() or '')
  except Exception:continue
  stack=[d]
  while stack:
   z=stack.pop()
   if isinstance(z,list):stack.extend(z);continue
   if not isinstance(z,dict):continue
   stack.extend(z.values());ty=z.get('@type');tys=ty if isinstance(ty,list) else [ty]
   if any(str(x).lower()=='product' for x in tys):
    meta['sku']=str(z.get('sku') or z.get('mpn') or meta['sku']);meta['name']=str(z.get('name') or meta['name']);im=z.get('image')
    if isinstance(im,str):imgs.append(urljoin(r.url,im))
    elif isinstance(im,list):
     for x in im:
      if isinstance(x,str):imgs.append(urljoin(r.url,x))
      elif isinstance(x,dict) and x.get('url'):imgs.append(urljoin(r.url,x['url']))
 for img in soup.find_all('img'):
  for a in ('data-zoom-image','data-large-image','data-src','data-original'):
   if img.get(a):imgs.append(urljoin(r.url,img[a]))
 seen=[]
 for x in imgs:
  x=html.unescape(x).replace('\\/','/')
  if x.startswith(('http://','https://')) and x not in seen:seen.append(x)
 return meta,seen[:25]

def query(rec):
 name=rec['name'];sku=rec.get('sku','');cat=rec['category'];n=name.replace('Whi',' White').replace('Blk',' Black').replace('Mln',' Melon').replace('VGr',' Varsity Green').replace('VBlu',' Varsity Blue').replace('Con',' Concrete').replace('Cha',' Charcoal').replace('Cntn',' Cantaloupe')
 if cat=='Jibbitz':return f'"{name}" Crocs Jibbitz'
 if cat=='Crocs shoes':return f'"{sku}" Crocs {n}'
 if cat=='ToGo':return f'"{name}" ToGo bag'
 return f'"{name}" Momentwear обувь'

def score(rec,c):
 hay=fold(' '.join([c.get('title',''),c.get('page',''),c.get('image',''),c.get('page_text','')[:20000],c.get('page_name',''),c.get('page_sku','')]))
 hc=compact(hay);sku=compact(rec.get('sku',''));ts=terms(rec['name']);matched=sum(t in hay for t in ts);ratio=matched/max(1,len(ts));s=ratio*90;reasons=[]
 if sku and (sku in hc or compact(c.get('page_sku',''))==sku):s+=90;reasons.append('exact_sku')
 if ratio>=.8:reasons.append('name_high')
 elif ratio>=.55:reasons.append('name_partial')
 if rec['category']=='Jibbitz' and any(x in hay for x in ('jibbitz','crocs charm','shoe charm')):s+=20;reasons.append('jibbitz_context')
 if rec['category']=='Crocs shoes' and 'crocs' in hay:s+=18;reasons.append('crocs_context')
 if rec['category']=='ToGo' and any(x in hay for x in ('togo','uniqbrand','silicone bag')):s+=20;reasons.append('togo_context')
 if rec['category']=='Momentwear' and any(x in hay for x in ('momentwear','moment wear','uniqbrand')):s+=20;reasons.append('momentwear_context')
 colors=[];raw=fold(rec['name'])
 for ru,en in COLOR_MAP.items():
  if fold(ru) in raw:colors.append(en)
 for en in ('black','white','blue','navy','pink','purple','green','yellow','orange','grey','gray','brown','khaki','lavender','cream','red'):
  if en in raw:colors.append(en)
 if colors:
  if any(x in hay for x in colors):s+=15;reasons.append('color')
  else:s-=8
 if ratio<.45 and 'exact_sku' not in reasons:s-=60
 return s,reasons,ratio

def process(rec):
 if rec['key'] in OVERRIDES:
  u,p=OVERRIDES[rec['key']];v=validate(u,p)
  if v:return {**base(rec),'confidence':'high','score':999,'source_page':p,'source_type':'verified_override','match_reason':'manual_verified',**v,'candidate_2':'','candidate_3':'','candidate_4':'','candidate_5':''}
 q=query(rec);candidates=[]
 for fn in (ddg_images,google_images,yandex_images):
  try:candidates.extend(fn(q))
  except Exception:pass
 for c in candidates:
  sc,rs,ra=score(rec,c);c.update(score=sc,reasons=rs,ratio=ra)
 for c in sorted(candidates,key=lambda x:x['score'],reverse=True)[:6]:
  if c.get('page') and c['score']>=25:
   meta,imgs=page_images(c['page']);ctx={**c,'page_text':meta.get('text',''),'page_name':meta.get('name',''),'page_sku':meta.get('sku','')};psc,prs,pra=score(rec,ctx)
   for im in imgs[:10]:candidates.append({'image':im,'page':meta.get('url') or c['page'],'title':meta.get('title',''),'engine':'parsed_page','page_text':meta.get('text',''),'page_name':meta.get('name',''),'page_sku':meta.get('sku',''),'score':psc+15,'reasons':prs,'ratio':pra})
 best={}
 for c in candidates:
  if 'score' not in c:
   sc,rs,ra=score(rec,c);c.update(score=sc,reasons=rs,ratio=ra)
  u=c.get('image','')
  if u and (u not in best or c['score']>best[u]['score']):best[u]=c
 verified=[]
 for c in sorted(best.values(),key=lambda x:x['score'],reverse=True)[:16]:
  if c['score']<30:continue
  v=validate(c['image'],c.get('page',''))
  if not v:continue
  c={**c,**v}
  if v['width']>=600 and v['height']>=600:c['score']+=8
  elif v['width']>=400 and v['height']>=400:c['score']+=4
  verified.append(c)
  if len(verified)>=5:break
 verified.sort(key=lambda x:x['score'],reverse=True);top=verified[0] if verified else None
 if not top:conf='not_found'
 elif top['score']>=125 and ('exact_sku' in top['reasons'] or top['ratio']>=.75):conf='high'
 elif top['score']>=85 and top['ratio']>=.55:conf='medium'
 else:conf='low'
 row=base(rec);row.update({'query':q,'confidence':conf})
 if top:row.update({'score':round(top['score'],1),'image_url':top['image_url'],'source_page':top.get('page',''),'source_type':top.get('engine',''),'width':top['width'],'height':top['height'],'content_type':top['content_type'],'match_reason':','.join(top['reasons'])})
 for i in range(1,5):row[f'candidate_{i+1}']=verified[i]['image_url'] if len(verified)>i else ''
 return row

def base(rec):return {'key':rec['key'],'sku':rec.get('sku',''),'name':rec['name'],'category':rec['category'],'rows':rec['rows'],'query':'','confidence':'','score':0,'image_url':'','source_page':'','source_type':'','width':0,'height':0,'content_type':'','match_reason':'','candidate_2':'','candidate_3':'','candidate_4':'','candidate_5':''}
def save(rows):
 (OUT/f'better_{SHARD}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 if rows:
  with (OUT/f'better_{SHARD}.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 recs=load_records();rows=[];print('shard',SHARD,'records',len(recs),flush=True)
 for i,r in enumerate(recs,1):
  try:x=process(r)
  except Exception as e:x=base(r);x['confidence']='error';x['match_reason']=type(e).__name__+':'+str(e)
  rows.append(x);save(rows);print(f"[{i}/{len(recs)}] {r['key']} {r['name']} => {x['confidence']} {x['score']} {x['image_url'][:100]}",flush=True);time.sleep(.15)
if __name__=='__main__':main()
