from __future__ import annotations
import json, re, subprocess
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
INDEX=SITE/'index.html'
text=INDEX.read_text()
errors=[]
required_sections=['top','problem','idea','architecture','contribution','experiments','results','failures','demo','scaling','safety','deepdive','artifacts','citation']
for section_id in required_sections:
    if f'id="{section_id}"' not in text: errors.append(f'missing section: {section_id}')
for cta in ['Paper','Code','Demo','Benchmark','Video']:
    if f'>{cta}</a>' not in text: errors.append(f'missing hero CTA: {cta}')
if 'Aura Yavary' not in text: errors.append('author name missing')
if not ('96.9%' in text and ('62.5%' in text or 'temporal + context' in text.lower())): errors.append('hero result line missing')

for required in ['Agent loop','RL / post-training loop','Recovery loop','Exact authority action','Live browser execution','Run gate']:
    if required not in text and required not in (SITE/'demo.html').read_text(): errors.append(f'missing required detail: {required}')
# Date-free public surface: allow package versions and metric numbers, but not calendar years.
if re.search(r'\b20\d{2}\b', text): errors.append('calendar year found in project homepage')

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a':
            d=dict(attrs); href=d.get('href')
            if href: self.hrefs.append(href)
p=Links(); p.feed(text)
missing=[]
for href in p.hrefs:
    if href.startswith(('#','http:','https:','mailto:','javascript:')): continue
    target=(SITE/href).resolve()
    if not target.exists(): missing.append(href)
if missing: errors.append('missing local links: '+', '.join(sorted(set(missing))))
for f in ['demo.html','benchmark.html','technical.html','blog.html','paper.pdf','dashboard.html','beliefweave-demo.mp4','downloads/beliefweave-code.zip','downloads/beliefweave-github-ready.zip','downloads/GITHUB_PUBLISHING.md','downloads/memworldbench_1000x100.jsonl.gz']:
    if not (SITE/f).exists(): errors.append(f'missing site artifact: {f}')
# Video must be playable and non-trivial.
video=SITE/'beliefweave-demo.mp4'
video_seconds=0.0
if video.exists():
    proc=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(video)],capture_output=True,text=True)
    try: video_seconds=float(proc.stdout.strip())
    except: video_seconds=0.0
    if video_seconds < 15: errors.append('demo video shorter than 15 seconds')
result={
    'ok': not errors,
    'sections': len(required_sections),
    'hero_ctas': 5,
    'author': 'Aura Yavary',
    'local_links_checked': len([h for h in p.hrefs if not h.startswith(('#','http:','https:','mailto:','javascript:'))]),
    'video_seconds': video_seconds,
    'errors': errors,
}
(ROOT/'results/site_contract.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if errors: raise SystemExit(1)
