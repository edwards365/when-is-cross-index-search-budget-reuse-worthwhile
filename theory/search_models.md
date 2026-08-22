# Search models and quantifiers

## Pure greedy and navigability

Pure greedy at current node \(x_t\) chooses the outgoing neighbor minimizing \(\delta(y,q)\), under a fixed tie rule, and moves only if it strictly improves the current value. A strictly monotone path merely exists when every edge on it decreases the potential; it need not be the path chosen by greedy.

Diwan et al. (NeurIPS 2024, Definition 3) call a directed graph navigable for a finite data set when their tie-broken Algorithm 1 returns every database target \(x_t\) from every database start. This quantifies over queries equal to stored points. It does not guarantee approximation for external \(q\), as the paper explicitly notes. HNSW/NSG/DiskANN heuristics do not claim worst-case navigability.

## Fixed-width beam search

The repository's bottom-layer reference search maintains:

- a min-priority queue of discovered, unexpanded candidates;
- a visited set, entered when a vertex is first discovered;
- a max-priority queue of at most `efSearch` best discovered results;
- expansion of the nearest candidate;
- termination when that candidate is worse than the current worst retained result and the result queue is full.

Thus `efSearch` bounds retained best results, while the visited and expanded counts are data-dependent and can exceed or differ from it. HNSW upper layers run the same SearchLayer with `ef=1`; the bottom layer uses the configured `efSearch`.

DABS instead views traversal order and stopping separately. Its parameter \(\gamma_{\rm DABS}\) stops only when \(k\) discovered points are better than the current candidate by a multiplicative \(1+\gamma_{\rm DABS}\). Its approximation theorem assumes an exactly navigable directed graph and a metric; practical HNSW is evaluated empirically as approximately navigable.

## Logical implications that fail

- A monotone path exists \(\centernot\Rightarrow\) pure greedy chooses it: a closer first branch can end in a local minimum.
- Beam success \(\centernot\Rightarrow\) a monotone path exists: finite-width search may retain and later expand a temporarily farther detour.
- Pure-greedy success does not supply a universal finite `efSearch` sufficient for a different queue/termination implementation; a bound requires controlling all competing frontier nodes.
- Effective resistance has no query in its definition, so no direct implication to any of these path predicates exists.

## Robust progress conditions

The weakest proved chain in this project is conditional:
\[
\text{reference bridge} + \text{score gap}
\Rightarrow \text{local selection}
\Rightarrow \text{retained cross edge}
\Rightarrow \text{existence of a monotone cross-cut path},
\]
where the last implication additionally assumes monotone paths on both sides and query-aligned progress across the edge. The unresolved link is that high leverage does not imply query alignment. It is therefore an experimental hypothesis measured by the fraction of high-score rejected/retained edges that produce progress on preregistered query traces.

To guarantee pure greedy, strengthen existence to **all-choice-safe \(\delta\)-navigation**: every improving neighbor the deterministic policy can choose remains in a state satisfying the same \(\delta\)-progress property. To guarantee a beam, additionally bound the number of higher-priority distractors or assert that the good frontier item remains retained until expansion. These are strong premises whose empirical prevalence must be reported.
