# Counterexamples and boundary examples

## C1: identical AUC, different operational risk

Take four examples ordered safe, safe, unsafe, unsafe. Scores \((4,3,2,1)\) and the strictly increasing transform \((0.8,0.6,0.4,0.2)\) have identical perfect AUC. At numerical cutoff 0.7, the first stops all four while the second stops only the safest example. Identical ranking quality therefore does not identify threshold risk without a calibrated threshold protocol.

## C2: high AUC with unsafe stopped tail

Let 980 safe points score 0.9, 10 unsafe points score 0.8, and 10 safe points score 0.1. Pairwise AUC remains near one because most safe–unsafe pairs are ordered correctly, but a policy stopping for score at least 0.8 includes all 10 unsafe points; its conditional failure rate is 10/990, which can exceed a stringent deployment target despite excellent ranking. Changing masses makes this gap arbitrarily consequential while preserving high AUC.

## C3: inversion count does not determine tax

Two target budgets can be inverted while both actions lie on a flat cost plateau, yielding zero cost penalty. The same single inversion with a large cost jump yields arbitrarily large penalty. Hence inversion rate supports a structural diagnosis but not a cost magnitude claim.

## C4: matching bound can be loose

In a long reversed chain every pair is inverted, but a vertex-disjoint matching uses at most half the vertices. A single monotone repair may impose costs distributed across the entire chain; pair penalties can overlap in the structural cause even though the matching avoids arithmetic double counting. The matching lower bound may therefore be far below the exact majorant tax.
