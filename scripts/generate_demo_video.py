from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import subprocess, textwrap, shutil

ROOT=Path(__file__).resolve().parents[1]
test_summary=json.loads((ROOT/'results'/'test_summary.json').read_text())
coverage_summary=json.loads((ROOT/'results'/'coverage.json').read_text())
TEST_COUNT=int(test_summary['passed'])
COVERAGE=float(coverage_summary['totals']['percent_covered'])
OUT=ROOT/'site'
FR=ROOT/'_video_frames'
if FR.exists(): shutil.rmtree(FR)
FR.mkdir()
W,H=1920,1080
BG=(8,10,13); PANEL=(16,20,25); TEXT=(243,246,247); MUTED=(169,179,188); ACCENT=(216,255,103); CYAN=(141,232,210); WARN=(255,207,112)
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold_path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def F(n,b=False): return ImageFont.truetype(bold_path if b else font_path,n)

def wrap(draw, text, font, maxw):
    words=text.split(); lines=[]; cur=''
    for word in words:
        test=(cur+' '+word).strip()
        if draw.textbbox((0,0),test,font=font)[2] <= maxw: cur=test
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def slide(title, subtitle='', kicker='BELIEFWEAVE', bullets=None, accent=ACCENT, diagram=None, metric=None, idx=0):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    # ambient glow
    for r in range(420,40,-20):
        alpha=int(18*(1-r/420)+2)
        col=(min(40,8+alpha),min(52,10+alpha),min(28,13+alpha//2))
        d.ellipse((W-r*1.2,-r*.7,W+r*.2,r*1.2),fill=col)
    d.text((110,90),kicker,font=F(30,True),fill=accent)
    y=170
    for line in wrap(d,title,F(72,True),1500):
        d.text((110,y),line,font=F(72,True),fill=TEXT); y+=88
    if subtitle:
        y+=12
        for line in wrap(d,subtitle,F(34),1450):
            d.text((110,y),line,font=F(34),fill=MUTED); y+=48
    if metric:
        y+=35
        d.rounded_rectangle((110,y,1120,y+180),radius=24,fill=PANEL,outline=(39,48,57),width=2)
        d.text((145,y+22),metric[0],font=F(52,True),fill=accent)
        for j,line in enumerate(wrap(d,metric[1],F(25),900)):
            d.text((145,y+92+j*34),line,font=F(25),fill=MUTED)
        y+=215
    if bullets:
        y+=20
        for b in bullets:
            d.ellipse((118,y+15,132,y+29),fill=accent)
            lines=wrap(d,b,F(29),1420)
            for j,line in enumerate(lines):
                d.text((155,y+j*40),line,font=F(29),fill=TEXT if j==0 else MUTED)
            y+=max(58,len(lines)*40+18)
    if diagram:
        y=max(y+30,650)
        x=110
        for j,(label,color) in enumerate(diagram):
            tw=d.textbbox((0,0),label,font=F(26,True))[2]+52
            d.rounded_rectangle((x,y,x+tw,y+72),radius=18,fill=PANEL,outline=color,width=3)
            d.text((x+26,y+18),label,font=F(26,True),fill=TEXT)
            x+=tw
            if j<len(diagram)-1:
                d.text((x+14,y+18),'→',font=F(32,True),fill=ACCENT); x+=66
    d.text((110,H-90),'Aura Yavary',font=F(27,True),fill=TEXT)
    d.text((W-340,H-90),f'{idx+1}/8',font=F(24),fill=MUTED)
    return im

slides=[
 slide('BeliefWeave','When Should Memory Be Allowed to Change Behavior?',idx=0,metric=('96.9% exact action','frozen 320-case BeliefShiftBench-v2 test split')),
 slide('The memory is relevant. Should it change behavior?','Retrieval answers what is related. Personalization needs a separate authority decision.',idx=1,diagram=[('RETRIEVE',MUTED),('AUTHORITY',ACCENT),('BEHAVIOR',CYAN)]),
 slide('A traceable belief-revision loop','Provenance, confidence, temporal validity, context, and conflict remain explicit.',idx=2,diagram=[('EVENT',MUTED),('MEMORY',MUTED),('STATE',CYAN),('GATE',ACCENT)]),
 slide('Stale memory → ABSTAIN','“User prefers sushi” can be semantically relevant while no longer current.',idx=3,diagram=[('RETRIEVE',MUTED),('STALE',WARN),('ABSTAIN',WARN)]),
 slide('Conflicting evidence → ASK','When authority is ambiguous, clarification is better than silent personalization.',idx=4,diagram=[('CONFLICT',WARN),('GATE',ACCENT),('ASK',CYAN)]),
 slide('Verified current belief → USE','Current, explicit, context-matched evidence can influence behavior.',idx=5,diagram=[('CURRENT',CYAN),('VERIFIED',CYAN),('USE',ACCENT)]),
 slide('Measured, not hand-waved','Controlled validation keeps the claim bounded.',idx=6,bullets=['640 BeliefShiftBench-v2 cases · 320 held-out test','96.9% exact USE / ASK / ABSTAIN on held-out cases','98.4% counterfactual intervention fidelity',f'{TEST_COUNT}/{TEST_COUNT} tests · {COVERAGE:.2f}% line coverage']),
 slide('Memory should earn behavioral authority.','Paper · Code · Demo · Benchmark · Dataset · Technical report',idx=7,metric=('BeliefWeave','by Aura Yavary')),
]
for i,im in enumerate(slides): im.save(FR/f'frame-{i:02d}.png')
concat=FR/'concat.txt'
with concat.open('w') as f:
    for i in range(len(slides)):
        f.write(f"file '{FR/f'frame-{i:02d}.png'}'\n")
        f.write('duration 4\n')
    f.write(f"file '{FR/f'frame-{len(slides)-1:02d}.png'}'\n")
out=OUT/'beliefweave-demo.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-vf','fps=30,format=yuv420p','-movflags','+faststart','-c:v','libx264','-crf','21',str(out)],check=True)
# poster
slides[0].resize((1280,720)).save(OUT/'beliefweave-demo-poster.png')
print(out)
