# Comparability verdicts

The comparison command returns a verdict and reasons; it never silently normalizes unlike work.

| Verdict | Meaning |
|---|---|
| `paired` | Same task contract, scorer, sample set, scenario strata, and compatible cost/runtime evidence. |
| `paired_quality_only` | Same task, scorer, and sample set, but cost/runtime evidence is missing or incompatible. |
| `partially_comparable` | Same task and scorer with only a strict subset of shared samples or strata. |
| `descriptive_only` | Related task but no lawful paired sample set or compatible scorer. Discuss separately; do not rank. |
| `incompatible` | Different task semantics, tolerance/scorer contract, or malformed evidence. |

The report lists shared and unpaired sample IDs and the exact fields that caused the verdict. Licensing and
media rights remain independent gates: technical compatibility does not authorize running or publishing a
comparison.
