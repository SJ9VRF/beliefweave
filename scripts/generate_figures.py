from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
OUT = ROOT / 'paper' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)


def load(name: str):
    return json.loads((RESULTS / name).read_text())


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(OUT / f'{name}.png', dpi=180, bbox_inches='tight')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)


def temporal_ablation():
    a = load('ablations.json')
    labels = ['Append-only', 'Latest-predicate', 'Full PWM']
    keys = ['append_only', 'latest_predicate', 'full_pwm']
    reversal = [100*a['reversal_retirement_accuracy'][k] for k in keys]
    expiry = [100*a['temporary_expiry_accuracy'][k] for k in keys]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    width = 0.36
    ax.bar([i-width/2 for i in x], reversal, width, label='Preference reversal')
    ax.bar([i+width/2 for i in x], expiry, width, label='Temporary expiry')
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 105)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Temporal-state ablation')
    ax.legend(frameon=False)
    save(fig, 'temporal_ablation')


def retrieval_comparison():
    r = load('retrieval_eval.json')
    labels = ['Hit@1', 'Hit@3', 'MRR']
    lexical = [100*r['lexical']['hit_at_1'], 100*r['lexical']['hit_at_3'], 100*r['lexical']['mrr']]
    semantic = [100*r['semantic_local']['hit_at_1'], 100*r['semantic_local']['hit_at_3'], 100*r['semantic_local']['mrr']]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    width = 0.36
    ax.bar([i-width/2 for i in x], lexical, width, label='Lexical baseline')
    ax.bar([i+width/2 for i in x], semantic, width, label='Local hybrid retriever')
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 105)
    ax.set_ylabel('Score (%)')
    ax.set_title(f"Retrieval benchmark (n={r['n_cases']})")
    ax.legend(frameon=False)
    save(fig, 'retrieval_comparison')


def ood_router():
    o = load('ood_robustness.json')['ood_router']
    by = o['by_label']
    labels = list(by)
    values = [100*by[k]['accuracy'] for k in labels]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.bar(labels, values)
    ax.axhline(100*o['accuracy'], linestyle='--', linewidth=1.2, label=f"Overall {100*o['accuracy']:.1f}%")
    ax.set_ylim(0, 105)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Observation router under held-out paraphrase families')
    ax.tick_params(axis='x', rotation=25)
    ax.legend(frameon=False)
    save(fig, 'ood_router')


def main():
    temporal_ablation()
    retrieval_comparison()
    ood_router()
    print(f'wrote figures to {OUT}')

if __name__ == '__main__':
    main()
