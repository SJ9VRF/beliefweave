from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'paper'/'figures';OUT.mkdir(parents=True,exist_ok=True)

def save(fig,name):
    fig.tight_layout();fig.savefig(OUT/f'{name}.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');plt.close(fig)

def main():
    r=json.loads((ROOT/'results'/'paper_grade_eval.json').read_text())
    names=['retrieval_only','confidence_only','temporal_context','metadata_score_no_hard_veto','cost_sensitive_authority','beliefweave'];labels=['Retrieval-only','Confidence','Temporal+context','Metadata score','Cost-sensitive','BeliefWeave'];x=range(len(names));w=.38
    fig,ax=plt.subplots(figsize=(7.2,3.5));ax.bar([i-w/2 for i in x],[r['systems'][n]['exact_action_accuracy'] for n in names],width=w,label='Exact action accuracy');ax.bar([i+w/2 for i in x],[r['systems'][n]['false_personalization_rate'] for n in names],width=w,label='False personalization rate');ax.set_xticks(list(x),labels,rotation=20,ha='right');ax.set_ylim(0,1.05);ax.set_ylabel('Rate');ax.legend(frameon=False,ncol=2);save(fig,'authority_baselines')
    rc=r['risk_coverage'];fig,ax=plt.subplots(figsize=(5.4,3.4));ax.plot([z['coverage'] for z in rc],[z['risk_false_use'] for z in rc],marker='o',markersize=2);ax.set_xlabel('Coverage (fraction accepted for USE)');ax.set_ylabel('False-use risk');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.grid(alpha=.2);save(fig,'risk_coverage')
    abl=r['component_ablations'];keys=['full_cost_sensitive','no_time','no_context','no_provenance','no_conflict','no_status'];labs=['Full','- time','- context','- provenance','- conflict','- status'];fig,ax=plt.subplots(figsize=(6,3.3));ax.bar(range(len(keys)),[abl[k]['cpr'] for k in keys]);ax.set_xticks(range(len(keys)),labs,rotation=20);ax.set_ylabel('CPR (lower is better)');save(fig,'authority_ablation_v2')
    h=json.loads((ROOT/'results'/'horizon_scaling.json').read_text())['rows'];fig,ax=plt.subplots(figsize=(5.5,3.3));ax.plot([z['turns'] for z in h],[z['p95_memory_update_ms'] for z in h],marker='o',label='Memory update p95');ax.plot([z['turns'] for z in h],[z['p95_gate_ms'] for z in h],marker='o',label='Authority gate p95');ax.set_xscale('log');ax.set_xlabel('Interaction horizon');ax.set_ylabel('Milliseconds');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'horizon_scaling')

    u=json.loads((ROOT/'results'/'unseen_composition.json').read_text()); labels=list(u['family_accuracy_mean']); vals=[u['family_accuracy_mean'][k] for k in labels]; fig,ax=plt.subplots(figsize=(7.2,3.5));ax.bar(range(len(labels)),vals);ax.set_ylim(0,1.05);ax.set_ylabel('Exact action accuracy');ax.set_xticks(range(len(labels)),[k.replace('_','\n') for k in labels],rotation=35,ha='right',fontsize=7);save(fig,'unseen_composition')
    s=json.loads((ROOT/'results'/'stochastic_stability.json').read_text()); snames=['retrieval_only','confidence_only','temporal_context','metadata_score_no_hard_veto','cost_sensitive_authority','beliefweave'];slabs=['Retrieval','Confidence','Time+ctx','Metadata','Cost-sensitive','BeliefWeave'];fig,ax=plt.subplots(figsize=(6.6,3.3));means=[s['systems'][n]['exact_action_accuracy_mean'] for n in snames];errs=[s['systems'][n]['exact_action_accuracy_std'] for n in snames];ax.bar(range(len(snames)),means,yerr=errs,capsize=3);ax.set_ylim(0,1.05);ax.set_ylabel('Mean exact accuracy across 30 seeds');ax.set_xticks(range(len(snames)),slabs,rotation=20,ha='right');save(fig,'stochastic_stability')

if __name__=='__main__':main()
