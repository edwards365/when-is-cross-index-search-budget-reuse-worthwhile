# Assumption dictionary

| Symbol / term | Exact meaning | Needed for | Not implied by |
|---|---|---|---|
| `Theta_obs` | finite observed build family | closed-world and fixed-design replay | a meta-environment law |
| `Pi` | stated law over environments | build-level probability and `delta_b` | nine historical builds |
| query iid/exchangeability | queries sampled within a fixed environment | binomial/conformal query bounds | build exchangeability |
| build iid/exchangeability | environments sampled from `Pi` | build-cluster confidence bounds | query iid |
| ordered budget | total order on actions | under-budget and conservative-cost comparisons | monotone loss |
| monotone loss | safety cannot worsen as budget increases | minimal safe budget representation | ordered costs alone |
| endpoint feasibility | a practical safe action exists under the named criterion | meaningful non-fallback allocation | empirical success at max budget |
| right censoring | safe threshold is above or unidentified on the grid | interval/conservative handling | endpoint impossibility |
| support coverage | target environment belongs to the modeled candidate/support set | closed-world recovery | small metadata distance |
| observation identifiability | observation laws distinguish relevant environments | environment testing | correct budget-response model |
| response regularity | nearby observable fingerprints imply nearby safe-budget response | structured open-world recovery | distinguishability alone |
| `Z0` | unlabeled static deployment metadata | metadata-only policies | runtime trajectory information |
| `Z1` | unlabeled deployable runtime/rebuild observation | possible structured recovery | ground truth or source Oracle |
| `Z2` | labeled target sentinel channel | target environment testing/calibration | unlabeled deployability |
| `Z3` | per-query labeled source budget Oracle | upper-bound replay | deployable base policy |
| fallback | separate safe/reject action with explicit cost/loss | abstention tradeoff | maximum budget |
| TV/KL/Hellinger | discrepancy between observation laws | testing lower bounds | novelty by itself |
| finite candidate count `M` | number of selected policies/hypotheses | multiplicity control | environment sample size `m` |
| `n` | calibration/evaluation queries per environment | within-build risk estimation | unseen-build coverage |
| `m` | independently sampled environments, only if assumed | meta-risk estimation | support correctness |
| `k` | target probes | target-channel testing error | misspecified response recovery |
| fixed design | inference restricted to named builds | descriptive robustness | population certificate |
| distribution-free | free of distributional form at a named sampling level | scoped coverage | simultaneous freedom at all levels |
| collision | similar deployable observation but materially different response under a frozen rule | empirical non-identification witness | causal equivalence |

## Status vocabulary

Theory is labeled only `FORMAL_PROOF_COMPLETE`, `RESTRICTED_PROPOSITION`, `PROOF_SKETCH`, `CONJECTURE`, or `REFUTED`. Empirical checks do not upgrade a proof status. Shapley values and paired contrasts are descriptive unless an intervention model is supplied.
