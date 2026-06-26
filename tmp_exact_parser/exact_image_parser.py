#!/usr/bin/env python3
from __future__ import annotations

import base64, csv, gzip, html, io, json, os, re, time, unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
SHARD = int(os.environ.get('SHARD', '0'))
SHARDS = int(os.environ.get('SHARDS', '1'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'
S = requests.Session()
S.headers.update({'User-Agent': UA, 'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'})

COLOR_MAP = {
    'Ð±ÐµÐ»Ñ‹Ð¹':'white','Ñ‡ÐµÑ€Ð½Ñ‹Ð¹':'black','Ñ‡Ñ‘Ñ€Ð½Ñ‹Ð¹':'black','Ð³Ð¾Ð»ÑƒÐ±Ð¾Ð¹':'blue','ÑÐ¸Ð½Ð¸Ð¹':'blue','Ð·ÐµÐ»ÐµÐ½Ñ‹Ð¹':'green','Ð·ÐµÐ»Ñ‘Ð½Ñ‹Ð¹':'green',
    'Ð¶ÐµÐ»Ñ‚Ñ‹Ð¹':'yellow','Ð¶Ñ‘Ð»Ñ‚Ñ‹Ð¹':'yellow','Ñ€Ð¾Ð·Ð¾Ð²Ñ‹Ð¹':'pink','ÑÐµÑ€Ñ‹Ð¹':'grey','ÐºÐ¾Ñ€Ð¸Ñ‡Ð½ÐµÐ²Ñ‹Ð¹':'brown','ÐºÑ€Ð°ÑÐ½Ñ‹Ð¹':'red',
    'Ð¾Ñ€Ð°Ð½Ð¶ÐµÐ²Ñ‹Ð¹':'orange','Ñ„Ð¸Ð¾Ð»ÐµÑ‚Ð¾Ð²Ñ‹Ð¹':'purple','Ð±ÐµÐ¶ÐµÐ²Ñ‹Ð¹':'beige','Ñ…Ð°ÐºÐ¸':'khaki','Ð»Ð°Ð²Ð°Ð½Ð´Ð¾Ð²Ñ‹Ð¹':'lavender'
}
STOP = set('crocs jibbitz charm charms shoe shoes adult adults for the and card style bag silicone togo momentwear Ð´Ð»Ñ Ð²Ð·Ñ€Ð¾ÑÐ»Ñ‹Ñ… Ð¾Ð±ÑƒÐ²ÑŒ Ñ†Ð²ÐµÑ‚ Ñ€Ð°Ð·Ð¼ÐµÑ€ Ð¼Ð¾Ð´ÐµÐ»ÑŒ Ð¼Ð¾Ð¼ÐµÐ½Ñ‚ ÑˆÑƒÐ· ÑÐ°Ð±Ð¾ Ð¿Ð¾Ð»ÑƒÐ±Ð¾Ñ‚Ð¸Ð½ÐºÐ¸ ÑˆÐ»ÐµÐ¿Ð°Ð½Ñ†Ñ‹ Ð²ÑŒÐµÑ‚Ð½Ð°Ð¼ÐºÐ¸ ÐºÑ€Ð¾ÑÑÐ¾Ð²ÐºÐ¸'.split())
BAD_WORDS = ('logo','placeholder','no-image','no_image','spacer','sprite','favicon','icon','loading','avatar')
GOOD_DOMAINS = ('crocs.com','crocs.co.uk','crocs.eu','crocs.com.au','crocs.com.br','crocs.com.uy','uniqbrand.shop','tradeinn.com','walmartimages.com','ebayimg.com','amazon','cloudfront','shopify','scene7','fcdn.app')

TRANSLIT = str.maketrans({
'Ð°':'a','Ð±':'b','Ð²':'v','Ð³':'g','Ð´':'d','Ðµ':'e','Ñ‘':'e','Ð¶':'zh','Ð·':'z','Ð¸':'i','Ð¹':'y','Ðº':'k','Ð»':'l','Ð¼':'m','Ð½':'n','Ð¾':'o','Ð¿':'p','Ñ€':'r','Ñ':'s','Ñ‚':'t','Ñƒ':'u','Ñ„':'f','Ñ…':'h','Ñ†':'ts','Ñ‡':'ch','Ñˆ':'sh','Ñ‰':'sch','ÑŠ':'','Ñ‹':'y','ÑŒ':'','Ñ':'e','ÑŽ':'yu','Ñ':'ya'
})

def fold(s: Any) -> str:
    s = unicodedata.normalize('NFKD', str(s or '')).lower().translate(TRANSLIT)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def compact(s: Any) -> str:
    return re.sub(r'[^a-z0-9]','',fold(s))

def tokens(s: Any) -> list[str]:
    return [x for x in fold(s).split() if len(x) >= 3 and x not in STOP]

def load_records() -> list[dict[str, Any]]:
    packed = (ROOT / 'records.json.gz.b64').read_text(encoding='utf-8').strip()
    data = gzip.decompress(base64.b64decode(packed))
    recs = json.loads(data.decode('utf-8'))
    return [r for i,r in enumerate(recs) if i % SHARDS == SHARD]

def safe_get(url: str, *, timeout=20, max_bytes=4_000_000, headers=None) -> requests.Response | None:
    try:
        r = S.get(url, timeout=timeout, allow_redirects=True, headers=headers or {}, stream=True)
        if r.status_code >= 400: return None
        content = bytearray()
        for chunk in r.iter_content(65536):
            if chunk: content.extend(chunk)
            if len(content) >= max_bytes: break
        r._content = bytes(content)
        r._content_consumed = True
        return r
    except Exception:
        return None

def validate_image(url: str, referer: str='') -> dict[str, Any] | None:
    if not url or not url.startswith(('http://','https://')): return None
    low = url.lower()
    if any(w in low for w in BAD_WORDS): return None
    hdr = {'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'}
    if referer: hdr['Referer'] = referer
    r = safe_get(url, timeout=25, max_bytes=9_000_000, headers=hdr)
    if not r: return None
    ctype = (r.headers.get('content-type') or '').split(';')[0].lower().strip()
    if not ctype.startswith('image/'):
        return None
    if len(r.content) < 3000: return None
    w=h=None; fmt=ctype.split('/')[-1]
    if ctype != 'image/svg+xml':
        try:
            im=Image.open(io.BytesIO(r.content)); w,h=im.size; fmt=(im.format or fmt).lower()
            if w < 250 or h < 250: return None
            if w/h > 6 or h/w > 6: return None
        except Exception: return None
    return {'image_url':r.url,'content_type':ctype,'width':w or 0,'height':h or 0,'bytes':len(r.content),'format':fmt}

def iter_json(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values(): yield from iter_json(v)
    elif isinstance(obj, list):
        for v in obj: yield from iter_json(v)

def extract_images_from_page(url: str) -> tuple[dict[str, Any], list[str]]:
    r=safe_get(url,timeout=22,max_bytes=5_000_000)
    if not r: return {},[]
    ctype=(r.headers.get('content-type') or '').lower()
    if 'html' not in ctype and not r.text.lstrip().startswith('<'): return {},[]
    soup=BeautifulSoup(r.text,'html.parser')
    title=(soup.title.get_text(' ',strip=True) if soup.title else '')
    text=soup.get_text(' ',strip=True)[:300000]
    meta={'url':r.url,'title':title,'text':text,'sku':'','name':''}
    images=[]
    for prop in ('og:image','og:image:secure_url','twitter:image','twitter:image:src'):
        for tag in soup.find_all('meta',attrs={'property':prop})+soup.find_all('meta',attrs={'name':prop}):
            v=tag.get('content');
            if v: images.append(urljoin(r.url,v))
    for script in soup.find_all('script',attrs={'type':re.compile('ld\+json',re.I)}):
        try: data=json.loads(script.string or script.get_text() or '')
        except Exception: continue
        for d in iter_json(data):
            typ=d.get('@type')
            types=typ if isinstance(typ,list) else [typ]
            if any(str(x).lower()=='product' for x in types):
                meta['sku']=str(d.get('sku') or d.get('mpn') or meta['sku'])
                meta['name']=str(d.get('name') or meta['name'])
                im=d.get('image')
                if isinstance(im,str): images.append(urljoin(r.url,im))
                elif isinstance(im,list):
                    for x in im:
                        if isinstance(x,str): images.append(urljoin(r.url,x))
                        elif isinstance(x,dict) and x.get('url'): images.append(urljoin(r.url,x['url']))
                elif isinstance(im,dict) and im.get('url'): images.append(urljoin(r.url,im['url']))
    attrs=('data-zoom-image','data-large_image','data-src','data-original','src')
    for img in soup.find_all('img'):
        for a in attrs:
            v=img.get(a)
            if v and not str(v).startswith('data:'): images.append(urljoin(r.url,str(v)))
        for a in ('srcset','data-srcset'):
            v=img.get(a)
            if v:
                parts=[]
                for item in str(v).split(','):
                    bits=item.strip().split()
                    if bits:
                        weight=int(re.sub(r'\D','',bits[-1]) or 0) if len(bits)>1 else 0
                        parts.append((weight,bits[0]))
                if parts: images.append(urljoin(r.url,max(parts)[1]))
    ded=[]; seen=set()
    for x in images:
        x=html.unescape(x).replace('\\/','/')
        if x not in seen and x.startswith(('http://','https://')):
            seen.add(x); ded.append(x)
    return meta,ded[:40]

def score_text(rec: dict[str,Any]²È="25ÉÍ•Èœ¤ì½ÕÐõmt(€€€™½È±¤¥¸Í½ÕÀ¹Í•±•Ð ±¤¹‰}…±¼œ¤è(€€€€€€€„õ±¤¹Í•±•Ñ}½¹”  È„œ¤(€€€€€€€¥˜¹½Ð„è½¹Ñ¥¹Õ”(€€€€€€€½ÕÐ¹…ÁÁ•¹¡ìÁ…”œé„¹•Ð ¡É•˜œ°œœ¤°Ñ¥Ñ±”œé„¹•Ñ}Ñ•áÐ œ€œ±ÍÑÉ¥ÀõQÉÕ”¤°Í¹¥ÁÁ•Ðœé±¤¹•Ñ}Ñ•áÐ œ€œ±ÍÑÉ¥ÀõQÉÕ”¥ô¤(€€€É•ÑÕÉ¸½ÕÑlèÄÁt()‘•˜ÅÕ•É¥•Ì¡É•Œè‘¥ÑmÍÑÈ±¹åt¤€´ø±¥ÍÑmÍÑÉtè(€€€Í­ÔõÉ•Œ¹•Ð Í­Ôœ°œœ¤ì¹…µ”õÉ•Œ¹•Ð ¹…µ”œ°œœ¤ì…ÐõÉ•Œ¹•Ð …Ñ•½Éäœ¤(€€€ÅÌõmt(€€€¥˜…Ðôô)¥‰‰¥Ñèœè(€€€€€€€¥˜Í­ÔèÅÌ€¬ôm˜œ‰íÍ­Õôˆ€‰í¹…µ•ôˆœ±˜œ‰íÍ­ÕôˆÉ½Ì)¥‰‰¥Ñèœ±˜œ‰í¹…µ•ôˆÉ½Ì)¥‰‰¥Ñèt(€€€€€€€•±Í”èÅÌ€¬ôm˜œ‰í¹…µ•ôˆÉ½Ì)¥‰‰¥Ñèt(€€€•±¥˜…ÐôôÉ½ÌÍ¡½•Ìœè(€€€€€€€ÅÌ€¬ôm˜œ‰íÍ­ÕôˆÉ½Ìœ±˜œ‰í¹…µ•ôˆÉ½Ìœ±˜íÍ­Õôí¹…µ•ôt(€€€•±¥˜…ÐôôQ½¼œè(€€€€€€€ÅÌ€¬ôm˜œ‰íÍ­Õôˆ€‰í¹…µ•ôˆœ±˜œ‰í¹…µ•ôˆQ½¼Í¥±¥½¹”œ±˜Í¥Ñ”éÕ¹¥Å‰É…¹¹Í¡½À€‰í¹…µ•ôˆt(€€€•±Í”è(€€€€€€€±…Ñ¥¸õ™½±¡¹…µ”¤(€€€€€€€ÅÌ€¬ôm˜œ‰íÍ­Õôˆ€‰í¹…µ•ôˆœ±˜œ‰íÍ­Õôˆ5½µ•¹ÑÝ•…Èœ±˜œ‰í±…Ñ¥¹ôˆ5½µ•¹ÑÝ•…Èt(€€€Í••¸õmt(€€€™½ÈÄ¥¸ÅÌè(€€€€€€€¥˜Ä¹½Ð¥¸Í••¸èÍ••¸¹…ÁÁ•¹¡Ä¤(€€€É•ÑÕÉ¸Í••¹lèÍt()‘•˜‘¥É•Ñ}É½Í}ÕÉ±Ì¡É•Œè‘¥ÑmÍÑÈ±¹åt¤€´ø±¥ÍÑmÍÑÉtè(€€€Í­ÔõÉ•Œ¹•Ð Í­Ôœ°œœ¤(€€€´õÉ”¹™Õ±±µ…Ñ ¡Èœ¡q‘ìÔ°Ùô¤´¡mµhÀ´åuìÍô¤œ±Í­Ô±É”¹$¤(€€€¥˜¹½Ð´èÉ•ÑÕÉ¸mt(€€€ÍÑå±”±½±½Èõ´¹É½ÕÁÌ ¤(€€€‰…Í”õ˜íÍÑå±•õ}í½±½Éôœ(€€€É•ÑÕÉ¸l(€€€€€˜¡ÑÑÁÌè¼½µ•‘¥„¹É½Ì¹½´½¥µ…•Ì½Ñ}Á‘Á¡•É¼½™}…ÕÑ¼±Å}…ÕÑ¼½ÁÉ½‘ÕÑÌ½í‰…Í•õ}1PÄÀÀ½É½Ìœ°(€€€€€˜¡ÑÑÁÌè¼½µ•‘¥„¹É½Ì¹½´½¥µ…•Ì½Ñ}Á‘Á¡•É¼½™}…ÕÑ¼±Å}…ÕÑ¼½ÁÉ½‘ÕÑÌ½í‰…Í•õ}1PÄÄÀ½É½Ìœ°(€€€€€˜¡ÑÑÁÌè¼½µ•‘¥„¹É½Ì¹½´½¥µ…•Ì½Ñ}Á‘Á¡•É¼½™}…ÕÑ¼±Å}…ÕÑ¼½ÁÉ½‘ÕÑÌ½í‰…Í•õ}1PÄÈÀ½É½Ìœ°(€€€€€˜¡ÑÑÁÌè¼½µ•‘¥„¹É½Ì¹½´½¥µ…•Ì½Ñ}Á‘Á¡•É¼½™}…ÕÑ¼±Å}…ÕÑ¼½ÁÉ½‘ÕÑÌ½í‰…Í•õ}1PÄÌÀ½É½Ìœ°(€€€t()‘•˜ÁÉ½•ÍÌ¡É•Œ°ÍÑ½É”°µ•‘¥„°Ñ•±•É…´¤è(€€€Á½½°õmt(€€€€Œá¥ÍÑ¥¹œÍÑ½É”ÁÉ½‘ÕÑÌ€¡¡¥¡•ÍÐÁÉ•¥Í¥½¸¤(€€€™½ÈÀ¥¸ÍÑ½É”è(€€€€€€€Í½É”±É•…Í½¸õÍ½É•}Ñ•áÐ¡É•Œ°˜‰íÁlÍ­ÔuôíÁl¹…µ”uôíÁlÁ•Éµ…±¥¹¬uôˆ±ÁlÍ­Ôt¤(€€€€€€€¥˜Í½É”øôÔÔè(€€€€€€€€€€€™½È¥´¥¸Ál¥µ…•Ìtè(€€€€€€€€€€€€€€€…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±¥´±ÁlÁ•Éµ…±¥¹¬t°Õ¹¥Å‰É…¹‘}ÍÑ½É”œ±˜‰íÁlÍ­ÔuôíÁl¹…µ”uôˆ°ÐÀ¤(€€€€Œ5•‘¥„±¥‰É…Éä(€€€™½È´¥¸µ•‘¥„è(€€€€€€€Ñàõ˜‰íµlÑ¥Ñ±”uôíµl…ÁÑ¥½¸uôíµlÍ±ÕœuôíµlÕÉ°uôˆ(€€€€€€€Í½É”±|õÍ½É•}Ñ•áÐ¡É•Œ±Ñà¤(€€€€€€€¥˜Í½É”øôÔÔè(€€€€€€€€€€€…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±µlÕÉ°t±µl±¥¹¬t°Õ¹¥Å‰É…¹‘}µ•‘¥„œ±Ñà°ÈÔ¤(€€€€ŒQ•±•É…´™½ÈÁÉ¥Ù…Ñ”‰É…¹‘Ì(€€€¥˜É•l…Ñ•½Éät¥¸€ Q½¼œ°5½µ•¹ÑÝ•…Èœ¤è(€€€€€€€Í½É•õmt(€€€€€€€™½ÈÀ¥¸Ñ•±•É…´è(€€€€€€€€€€€ÍŒ±|õÍ½É•}Ñ•áÐ¡É•Œ±ÁlÑ•áÐt¬œ€œ­ÁlÁ½ÍÐt¤(€€€€€€€€€€€¥˜ÍŒøôÌÔèÍ½É•¹…ÁÁ•¹ ¡ÍŒ±À¤¤(€€€€€€€™½ÈÍŒ±À¥¸Í½ÉÑ•¡Í½É•±É•Ù•ÉÍ”õQÉÕ”±­•äõ±…µ‰‘„àéálÁt¥lèÑtè(€€€€€€€€€€€™½È¥´¥¸Ál¥µ…•Ìtè(€€€€€€€€€€€€€€€…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±¥´±ÁlÁ½ÍÐt°Ñ•±•É…´œ±ÁlÑ•áÐt°ÈÀ¤(€€€€ŒÁÉ•‘¥Ñ…‰±”É½Ì8(€€€™½È¥´¥¸‘¥É•Ñ}É½Í}ÕÉ±Ì¡É•Œ¤è…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±¥´°¡ÑÑÁÌè¼½ÝÝÜ¹É½Ì¹½´¼œ°É½Í}‘¸œ±É•lÍ­Ôt¬œ€œ­É•l¹…µ”t°ÌÔ¤(€€€€ŒM•…É •¹¥¹•Ì½¹±ä¥˜¹¼…±É•…‘äÍÑÉ½¹œÑ•áÑÕ…°…¹‘¥‘…Ñ”(€€€ÁÉ•µ…àõµ…à¡málÍ½É”t™½Èà¥¸Á½½±t±‘•™…Õ±ÐôÀ¤(€€€¥˜ÁÉ•µ…àðÄÄÀè(€€€€€€€™½ÈÅ¤±Ä¥¸•¹Õµ•É…Ñ”¡ÅÕ•É¥•Ì¡É•Œ¤¤è(€€€€€€€€€€€¥µÌõ‰¥¹}¥µ…•Ì¡Ä¤(€€€€€€€€€€€™½ÈÉ…¹¬±à¥¸•¹Õµ•É…Ñ”¡¥µÍlèÄÉt¤è(€€€€€€€€€€€€€€€…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±ál¥µ…”t±álÁ…”t°‰¥¹}¥µ…”œ±álÑ¥Ñ±”t±µ…à À°ÄàµÉ…¹¬¤µÅ¤¨Ì¤(€€€€€€€€€€€€ŒA…ÉÍ”Ñ½ÀÉ•ÍÕ±ÐÁ…•Ì…¹•áÑÉ…Ð½É¥¥¹…°¥µ…•Ì(€€€€€€€€€€€™½ÈÉ…¹¬±à¥¸•¹Õµ•É…Ñ”¡‰¥¹}Ý•ˆ¡Ä¥lèÕt¤è(€€€€€€€€€€€€€€€µ•Ñ„±¥µ…•Ìõ•áÑÉ…Ñ}¥µ…•Í}™É½µ}Á…”¡álÁ…”t¤(€€€€€€€€€€€€€€€Ñàôœ€œ¹©½¥¸¡málÑ¥Ñ±”t±à¹•Ð Í¹¥ÁÁ•Ðœ°œœ¤±µ•Ñ„¹•Ð Ñ¥Ñ±”œ°œœ¤±µ•Ñ„¹•Ð ¹…µ”œ°œœ¤±µ•Ñ„¹•Ð Í­Ôœ°œœ¤±µ•Ñ„¹•Ð Ñ•áÐœ°œœ¥lèàÀÀÁut¤(€€€€€€€€€€€€€€€ÁÍ½É”±|õÍ½É•}Ñ•áÐ¡É•Œ±Ñà±µ•Ñ„¹•Ð Í­Ôœ°œœ¤¤(€€€€€€€€€€€€€€€¥˜ÁÍ½É”øôÐÔè(€€€€€€€€€€€€€€€€€€€™½È¥´¥¸¥µ…•ÍlèÄÁtè…‘‘}…¹‘¥‘…Ñ”¡Á½½°±É•Œ±¥´±µ•Ñ„¹•Ð ÕÉ°œ¤½ÈálÁ…”t°Á…ÉÍ•‘}Á…”œ±Ñà°ÈÔµÉ…¹¬¤(€€€€€€€€€€€¥˜…¹ä¡álÍ½É”tøôÄÈÔ™½Èà¥¸Á½½°¤è‰É•…¬(€€€€€€€€€€€Ñ¥µ”¹Í±••À ¸ÈÔ¤(€€€€Œ‘•‘ÕÁ”…¹Ù…±¥‘…Ñ”‰äÍ½É”(€€€‰•ÍÑ}‰å}ÕÉ°õíô(€€€™½ÈŒ¥¸Á½½°è(€€€€€€€­•äõlÉ…Ý}¥µ…•}ÕÉ°t(€€€€€€€¥˜­•ä¹½Ð¥¸‰•ÍÑ}‰å}ÕÉ°½ÈlÍ½É”tù‰•ÍÑ}‰å}ÕÉ±m­•åulÍ½É”tè‰•ÍÑ}‰å}ÕÉ±m­•åtõŒ(€€€É…¹­•õÍ½ÉÑ•¡‰•ÍÑ}‰å}ÕÉ°¹Ù…±Õ•Ì ¤±­•äõ±…µ‰‘„àéálÍ½É”t±É•Ù•ÉÍ”õQÉÕ”¤(€€€Ù•É¥™¥•õmt(€€€™½ÈŒ¥¸É…¹­•‘lèÌÁtè(€€€€€€€ØõÙ…±¥‘…Ñ•}¥µ…”¡lÉ…Ý}¥µ…•}ÕÉ°t±lÍ½ÕÉ•}Á…”t¤(€€€€€€€¥˜¹½ÐØè½¹Ñ¥¹Õ”(€€€€€€€Œõì¨©Œ°¨©Ùô(€€€€€€€€ŒÅÕ…±¥Ñä‰½¹ÕÌ(€€€€€€€¥˜lÝ¥‘Ñ tøôÜÀÀ…¹l¡•¥¡ÐtøôÜÀÀèlÍ½É”t¬ôà(€€€€€€€•±¥˜lÝ¥‘Ñ tøôÔÀÀ…¹l¡•¥¡ÐtøôÔÀÀèlÍ½É”t¬ôÐ(€€€€€€€Ù•É¥™¥•¹…ÁÁ•¹¡Œ¤(€€€€€€€¥˜±•¸¡Ù•É¥™¥•¤øôÔ…¹Ù•É¥™¥•‘lÁulÍ½É”tøôÄÀÀè‰É•…¬(€€€Ù•É¥™¥•¹Í½ÉÐ¡­•äõ±…µ‰‘„àéálÍ½É”t±É•Ù•ÉÍ”õQÉÕ”¤(€€€Ñ½ÀõÙ•É¥™¥•‘lÁt¥˜Ù•É¥™¥••±Í”9½¹”(€€€¥˜¹½ÐÑ½Àè(€€€€€€€½¹˜ô¹½Ñ}™½Õ¹œ(€€€•±¥˜Ñ½ÁlÍ½É”tøôÄÄÔ…¹€ •á…Ñ}Í­Ôœ¥¸Ñ½ÁlÉ•…Í½¹Ìt½È€¹…µ•}¡¥ œ¥¸Ñ½ÁlÉ•…Í½¹Ìt¤è½¹˜ô¡¥ œ(€€€•±¥˜Ñ½ÁlÍ½É”tøôàÀè½¹˜ôµ•‘¥Õ´œ(€€€•±Í”è½¹˜ô±½Üœ(€€€É•ÑÕÉ¸ì(€€€€€€­•äœéÉ•l­•ät°Í­ÔœéÉ•Œ¹•Ð Í­Ôœ°œœ¤°¹…µ”œéÉ•l¹…µ”t°…Ñ•½ÉäœéÉ•l…Ñ•½Éät°É½ÝÌœéÉ•lÉ½ÝÌt°(€€€€€€½¹™¥‘•¹”œé½¹˜°‰•ÍÑ}¥µ…”œéÑ½Ál¥µ…•}ÕÉ°t¥˜Ñ½À•±Í”€œœ°€Í½ÕÉ•}Á…”œéÑ½ÁlÍ½ÕÉ•}Á…”t¥˜Ñ½À•±Í”€œœ°(€€€€€€Í½ÕÉ•}ÑåÁ”œéÑ½ÁlÍ½ÕÉ•}ÑåÁ”t¥˜Ñ½À•±Í”€œœ°€Í½É”œéÉ½Õ¹¡Ñ½ÁlÍ½É”t°Ä¤¥˜Ñ½À•±Í”€À°(€€€€€€Ý¥‘Ñ œéÑ½ÁlÝ¥‘Ñ t¥˜Ñ½À•±Í”€À°¡•¥¡ÐœéÑ½Ál¡•¥¡Ðt¥˜Ñ½À•±Í”€À°½¹Ñ•¹Ñ}ÑåÁ”œéÑ½Ál½¹Ñ•¹Ñ}ÑåÁ”t¥˜Ñ½À•±Í”€œœ°(€€€€€€µ…Ñ¡}É•…Í½¸œèœ°œ¹©½¥¸¡Ñ½ÁlÉ•…Í½¹Ìt¤¥˜Ñ½À•±Í”€œœ°(€€€€€€…¹‘¥‘…Ñ•|ÈœéÙ•É¥™¥•‘lÅul¥µ…•}ÕÉ°t¥˜±•¸¡Ù•É¥™¥•¤øÄ•±Í”€œœ°(€€€€€€…¹‘¥‘…Ñ•|ÌœéÙ•É¥™¥•‘lÉul¥µ…•}ÕÉ°t¥˜±•¸¡Ù•É¥™¥•¤øÈ•±Í”€œœ°(€€€€€€…¹‘¥‘…Ñ•|ÐœéÙ•É¥™¥•‘lÍul¥µ…•}ÕÉ°t¥˜±•¸¡Ù•É¥™¥•¤øÌ•±Í”€œœ°(€€€€€€…¹‘¥‘…Ñ•|ÔœéÙ•É¥™¥••‘lÑul¥µ…•}ÕÉ°t¥˜±•¸¡Ù•É¥™¥•¤øÐ•±Í”€œœ°(€€€ô()‘•˜µ…¥¸ ¤è(€€€É•Ìõ±½…‘}É•½É‘Ì ¤(€€€ÁÉ¥¹Ð¡˜M¡…ÉíM!Iô½íM!IMôèí±•¸¡É•Ì¥ôÉ•½É‘Ìœ±™±ÕÍ õQÉÕ”¤(€€€ÍÑ½É”õÉ…Ý±}ÍÑ½É•}…Á¤ ¤ìÁÉ¥¹Ð ÍÑ½É”ÁÉ½‘ÕÑÌœ±±•¸¡ÍÑ½É”¤±™±ÕÍ õQÉÕ”¤(€€€µ•‘¥„õÉ…Ý±}µ•‘¥…}…Á¤ ¤ìÁÉ¥¹Ð µ•‘¥„œ±±•¸¡µ•‘¥„¤±™±ÕÍ õQÉÕ”¤(€€€Ñ•±•É…´õÉ…Ý±}Ñ•±•É…´ ¤ìÁÉ¥¹Ð Ñ•±•É…´Á½ÍÑÌœ±±•¸¡Ñ•±•É…´¤±™±ÕÍ õQÉÕ”¤(€€€É•ÍÕ±ÑÌõmt(€€€™½È¤±É•Œ¥¸•¹Õµ•É…Ñ”¡É•Ì°Ä¤è(€€€€€€€ÑÉäèÉ½ÜõÁÉ½•ÍÌ¡É•Œ±ÍÑ½É”±µ•‘¥„±Ñ•±•É…´¤(€€€€€€€•á•ÁÐá•ÁÑ¥½¸…Ì”è(€€€€€€€€€€€É½Üõì­•äœéÉ•l­•ät°Í­ÔœéÉ•Œ¹•Ð Í­Ôœ°œœ¤°¹…µ”œéÉ•l¹…µ”t°…Ñ•½ÉäœéÉ•l…Ñ•½Éät°É½ÝÌœéÉ•lÉ½ÝÌt°½¹™¥‘•¹”œè•ÉÉ½Èœ°‰•ÍÑ}¥µ…”œèœœ°Í½ÕÉ•}Á…”œèœœ°Í½ÕÉ•}ÑåÁ”œèœœ°Í½É”œèÀ°Ý¥‘Ñ œèÀ°¡•¥¡ÐœèÀ°½¹Ñ•¹Ñ}ÑåÁ”œèœœ°µ…Ñ¡}É•…Í½¸œéÑåÁ”¡”¤¹}}¹…µ•}|¬œèœ­ÍÑÈ¡”¤°…¹‘¥‘…Ñ•|Èœèœœ°…¹‘¥‘…Ñ•|Ìœèœœ°…¹‘¥‘…Ñ•|Ðœèœœ°…¹‘¥‘…Ñ•|Ôœèœô(€€€€€€€É•ÍÕ±ÑÌ¹…ÁÁ•¹¡É½Ü¤(€€€€€€€ÁÉ¥¹Ð¡˜‰mí¥ô½í±•¸¡É•Ì¥õtíÉ•l­•äuô€ôøíÉ½Ýl½¹™¥‘•¹”uôíÉ½ÝlÍ½É”uôíÉ½Ýl‰•ÍÑ}¥µ…”ulèÄÀÁuôˆ±™±ÕÍ õQÉÕ”¤(€€€€€€€Ñ¥µ”¹Í±••À ¸ÄÔ¤(€€€€¡=UP½˜É•ÍÕ±ÑÍ}íM!Iô¹©Í½¸œ¤¹ÝÉ¥Ñ•}Ñ•áÐ¡©Í½¸¹‘ÕµÁÌ¡É•ÍÕ±ÑÌ±•¹ÍÕÉ•}…Í¥¤õ…±Í”±¥¹‘•¹ÐôÈ¤±•¹½‘¥¹œôÕÑ˜´àœ¤(€€€™¥•±‘Ìõ±¥ÍÐ¡É•ÍÕ±ÑÍlÁt¹­•åÌ ¤¤¥˜É•ÍÕ±ÑÌ•±Í”mt(€€€Ý¥Ñ €¡=UP½˜É•ÍÕ±ÑÍ}íM!Iô¹ÍØœ¤¹½Á•¸ Üœ±•¹½‘¥¹œôÕÑ˜´àµÍ¥œœð¹•Ý±¥¹”ôœœ¤…Ì˜è(€€€€€€€ÜõÍØ¹¥Ñ]É¥Ñ•È¡˜±™¥•±‘¹…µ•Ìõ™¥•±‘Ì¤ìÜ¹ÝÉ¥Ñ•¡•…‘•È ¤ìÜ¹ÝÉ¥Ñ•É½ÝÌ¡É•ÍÕ±ÑÌ¤(€€€ÍÕµµ…ÉäõìÍ¡…ÉœéM!I°Ñ½Ñ…°œé±•¸¡É•ÍÕ±ÑÌ¤°¡¥ œéÍÕ´¡ál½¹™¥‘•¹”tôô¡¥ œ™½Èà¥¸É•ÍÕ±ÑÌ¤°µ•‘¥Õ´œéÍÕ´¡ál½¹™¥‘•¹”tôôµ•‘¥Õ´œ™½Èà¥¸É•ÍÕ±ÑÌ¤°±½ÜœéÍÕ´¡ál½¹™¥‘•¹”tôô±½Üœ™½Èà¥¸É•ÍÕ±ÑÌ¤°¹½Ñ}™½Õ¹œéÍÕ´¡ál½¹™¥‘•¹”tôô¹½Ñ}™½Õ¹œ™½Èà¥¸É•ÍÕ±ÑÌ¤°•ÉÉ½ÈœéÍÕ´¡ál½¹™¥‘•¹”tôô•ÉÉ½Èœ™½Èà¥¸É•ÍÕ±ÑÌ¤°‰ÍÑ½É•}ÁÉ½‘ÕÑÌˆé±•¸¡ÍÑ½É”¤°‰µ•‘¥„ˆé±•¸¡µ•‘¥„¤°‰Ñ•±•É…´ˆé±•¸¡Ñ•±•É…´¥ô(€€€€¡=UP½˜ÍÕµµ…Éå}íM!Iô¹©Í½¸œ¤¹ÝÉ¥Ñ•}Ñ•áÐ¡©Í½¸¹‘ÕµÁÌ¡ÍÕµµ…Éä±•¹ÍÕÉ•}…Í¥¤õ…±Í”±¥¹‘•¹ÐôÈ¤±•¹½‘¥¹œôÕÑ˜´àœ¤(€€€ÁÉ¥¹Ð¡ÍÕµµ…Éä±™±ÕÍ õQÉÕ”¤()¥˜}}¹…µ•}|ôô}}µ…¥¹}|œèµ…¥¸ ¤