# Cross-family final report

### sift_100k
- 24 builds, 552 directed pairs, 750 clean queries; action grid 16/32/64/128/256/512.
- finite variation=0.910666667, endpoint variation=0.005333333, inclusive variation=0.910666667, unresolved=0.000722222.
- absolute/reference/incremental risk=0.236714975845/0.000722222222/0.235992753623; bootstrap CI=[0.227801690821,0.243872403382]; top-1% deletion=0.234269405055; LOBO=[0.235343873518,0.236598155468].

### arxiv_nomic_100k
- 24 builds, 552 directed pairs, 750 clean queries; action grid 16/32/64/128/256/512.
- finite variation=0.758666667, endpoint variation=0.018666667, inclusive variation=0.758666667, unresolved=0.001666667.
- absolute/reference/incremental risk=0.179323671498/0.001666666667/0.177657004831; bootstrap CI=[0.168569927536,0.186756219807]; top-1% deletion=0.175348646432; LOBO=[0.177140974967,0.178210803689].

The six-cell table keeps native action families separate. Positive directions are evidence within registered scopes; raw budget values are not equated across implementations. Vamana h8/h9 remain not estimable from frozen hit counts.
