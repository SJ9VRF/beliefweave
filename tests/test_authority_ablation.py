from benchmark.authority_ablation_bench import evaluate
def test_authority_ablation():
 r=evaluate();s=r['systems'];assert r['n']==200;assert s['beliefweave']['false_personalization_rate']==0;assert s['beliefweave']['use_precision']==1;assert s['beliefweave']['use_recall']==1;assert s['beliefweave']['cpr']<s['confidence_only']['cpr']<s['retrieval_only']['cpr'];assert len(r['threshold_sweep'])>=20
