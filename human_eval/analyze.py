from __future__ import annotations
import argparse,csv,json,math
from collections import Counter

def wilson(k,n,z=1.96):
    if not n:return [0,0]
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [c-h,c+h]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('csv');a=ap.parse_args();rows=list(csv.DictReader(open(a.csv)));prefs=Counter(r['overall_preference'] for r in rows); decisive=prefs['A']+prefs['B'];
    out={'n_annotations':len(rows),'overall_preference':prefs,'A_preference_among_decisive':prefs['A']/decisive if decisive else None,'A_preference_95ci':wilson(prefs['A'],decisive) if decisive else None};print(json.dumps(out,indent=2,default=dict))
if __name__=='__main__':main()
