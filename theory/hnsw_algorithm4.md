# HNSW Algorithm 4: audited semantics

Source checked: Malkov and Yashunin, TPAMI manuscript, Algorithm 4 and Sections 3, 4, and 4.2 (author preprint arXiv:1603.09320; DOI 10.1109/TPAMI.2018.2889473).

Inputs are base element \(q\), candidate set/queue \(C\), budget \(M\), layer \(\ell_c\), and Boolean flags `extendCandidates` and `keepPrunedConnections`. The symbol \(q\) here is an inserted/base element, not necessarily an external query.

1. Initialize accepted set \(R=\varnothing\), working queue \(W=C\), and discarded queue \(W_d=\varnothing\).
2. If `extendCandidates`, add previously absent layer-\(\ell_c\) neighbors of every candidate to \(W\).
3. While \(W\ne\varnothing\) and \(|R|<M\), extract the candidate \(e\) nearest to the base \(q\).
4. Accept \(e\) exactly when
   \[
   d_X(e,q)<d_X(e,r)\quad\text{for every }r\in R.
   \]
   Otherwise put it in \(W_d\). For \(R=\varnothing\), the condition is vacuous.
5. If `keepPrunedConnections`, fill any remaining slots by repeatedly taking the discarded item nearest to \(q\).
6. Return \(R\).

The paper's line 11 says that \(e\) is closer to \(q\) than to any element already in \(R\); the prose in Section 3 confirms the pairwise interpretation above. This is a relative-neighborhood-style geometric diversification rule. It neither computes graph effective resistance nor asks whether \(e\) decreases distance to a future external query.

Algorithm 1 adds the selected connections bidirectionally, then invokes the same selector to shrink a neighbor's list if it exceeds \(M_{\max}\) (or \(M_{\max,0}\) at layer zero). Thus a locally accepted edge can later disappear through reverse pruning.

The paper's logarithmic scaling discussion is conditional: the strict analysis substitutes exact Delaunay graphs and assumes the closest element at a layer is found; approximate graphs use bottom-layer backtracking and an empirical observation that the required `ef` saturates on tested low-dimensional data. The authors explicitly call for more analytical evidence in high dimensions. This is not a distribution-free worst-case logarithmic theorem for practical HNSW.
