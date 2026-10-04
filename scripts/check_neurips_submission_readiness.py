from __future__ import annotations
import json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tex=ROOT/'paper/BELIEFWEAVE.tex'
pdf=ROOT/'paper/BELIEFWEAVE.pdf'
style=ROOT/'paper/neurips_2026.sty'
text=tex.read_text(errors='replace')
uses_official=bool(re.search(r'\\usepackage(?:\[[^\]]*\])?\{neurips_2026\}',text))
uses_geometry='\\usepackage' in text and '{geometry}' in text
pages=None
if pdf.exists():
    try:
        out=subprocess.check_output(['pdfinfo',str(pdf)],text=True,stderr=subprocess.DEVNULL)
        m=re.search(r'^Pages:\s+(\d+)',out,re.M); pages=int(m.group(1)) if m else None
    except Exception:
        pass
blockers=[]
if not style.exists(): blockers.append('official neurips_2026.sty is not bundled')
if not uses_official: blockers.append('paper source does not load neurips_2026.sty')
if uses_geometry: blockers.append('paper source uses custom geometry rather than the official template')
if pages is not None and pages>9: blockers.append(f'main research manuscript is {pages} pages; official main-text budget is 9')
out={
  'ready_for_official_neurips_template_submission': not blockers,
  'research_manuscript_exists': pdf.exists(),
  'research_manuscript_pages': pages,
  'official_style_file_present': style.exists(),
  'source_loads_official_style': uses_official,
  'custom_geometry_detected': uses_geometry,
  'blockers': blockers,
  'claim_policy':'The research manuscript may be scientifically submission-oriented, but it is not labeled NeurIPS-format-ready until the official style is present and used without layout overrides.'
}
(ROOT/'results/neurips_submission_readiness.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
