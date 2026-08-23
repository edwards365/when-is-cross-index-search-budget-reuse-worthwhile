# Replay Gate R0 preliminary mechanism analysis

Status: **PENDING_FINAL_R0_ADJUDICATION**. This report contains the frozen structural replay and read-only design-dev trace diagnostics; it does not authorize E0.

- Structural events: 2304 across 9 dataset/seed runs.
- Matched route states: 5503.
- Reached sampled events: 1206 of 2304.
- Existing Original 100K indexes were loaded read-only; no graph was built or mutated.
- Formal test members accessed: false.

## GB-MPCC paired real-route differences

Positive values favor Geometry-Backbone-MPCC. Values are macro-averaged over sampled events reached by at least one frozen query/ef trace.

```text
        dataset  build_seed                        baseline  events  delta_strict_progress  delta_multiplicative_progress_eta_0_05  delta_beam_admissible  delta_expanded_later  delta_missed_true_neighbor_opportunity
arxiv_nomic_10k           7                      algorithm4     147               0.031063                                0.016019               0.019174              0.016991                                0.000000
arxiv_nomic_10k           7                        geometry     147               0.049867                               -0.011763               0.049745              0.030346                                0.000000
arxiv_nomic_10k           7                    maxmin_angle     147               0.157329                                0.076267               0.146690              0.056177                                0.000000
arxiv_nomic_10k           7              length_aware_angle     147               0.031063                                0.016019               0.019174              0.016991                                0.000000
arxiv_nomic_10k           7                           ggr_0     147               0.098446                                0.006398               0.092687              0.041857                                0.000000
arxiv_nomic_10k           7        geometry_backbone_random     147               0.029584                                0.007467               0.019947              0.017214                                0.000000
arxiv_nomic_10k           7 geometry_backbone_mpcc_shuffled     147               0.034092                                0.017277               0.024066              0.007736                                0.000000
arxiv_nomic_10k          17                      algorithm4     146               0.011988                                0.009673               0.012959              0.016575                                0.000000
arxiv_nomic_10k          17                        geometry     146               0.081478                                0.027559               0.069809              0.007598                                0.000000
arxiv_nomic_10k          17                    maxmin_angle     146               0.134419                                0.067765               0.143463              0.109463                                0.000000
arxiv_nomic_10k          17              length_aware_angle     146               0.011988                                0.009673               0.012959              0.016575                                0.000000
arxiv_nomic_10k          17                           ggr_0     146               0.088555                                0.030576               0.082411              0.023853                                0.000000
arxiv_nomic_10k          17        geometry_backbone_random     146               0.011901                                0.011724               0.022962              0.023291                                0.000000
arxiv_nomic_10k          17 geometry_backbone_mpcc_shuffled     146               0.031980                                0.015758               0.027470              0.011214                                0.000000
arxiv_nomic_10k          29                      algorithm4     147               0.008844                               -0.006276               0.029319              0.022092                                0.000000
arxiv_nomic_10k          29                        geometry     147               0.010166                               -0.021194               0.041713              0.019716                                0.000094
arxiv_nomic_10k          29                    maxmin_angle     147               0.117284                                0.042365               0.135900              0.078264                                0.000850
arxiv_nomic_10k          29              length_aware_angle     147               0.008844                               -0.006276               0.029319              0.022092                                0.000000
arxiv_nomic_10k          29                           ggr_0     147               0.036427                                0.001384               0.070479              0.034017                                0.000850
arxiv_nomic_10k          29        geometry_backbone_random     147               0.004465                                0.001433               0.025622              0.012782                                0.000000
arxiv_nomic_10k          29 geometry_backbone_mpcc_shuffled     147               0.008503                               -0.005709               0.018775              0.017463                                0.000000
   glove100_10k           7                      algorithm4     131               0.043943                                0.023039               0.023883              0.017342                                0.000402
   glove100_10k           7                        geometry     131               0.066178                                0.009717               0.062330              0.058467                               -0.002374
   glove100_10k           7                    maxmin_angle     131               0.124921                                0.017140               0.111100              0.090667                               -0.000466
   glove100_10k           7              length_aware_angle     131               0.043943                                0.023039               0.023883              0.017342                                0.000402
   glove100_10k           7                           ggr_0     131               0.059786                               -0.000060               0.067050              0.065677                               -0.002374
   glove100_10k           7        geometry_backbone_random     131               0.044585                                0.012162               0.020464              0.021020                                0.000402
   glove100_10k           7 geometry_backbone_mpcc_shuffled     131               0.022315                               -0.018764               0.015884              0.018268                                0.000402
   glove100_10k          17                      algorithm4     128               0.063627                                0.006697               0.070696              0.059960                                0.000000
   glove100_10k          17                        geometry     128               0.037253                                0.009475               0.062746              0.049845                                0.000000
   glove100_10k          17                    maxmin_angle     128               0.135475                                0.071006               0.139587              0.125287                                0.000000
   glove100_10k          17              length_aware_angle     128               0.063627                                0.006697               0.070696              0.059960                                0.000000
   glove100_10k          17                           ggr_0     128               0.052093                                0.018022               0.074920              0.057973                                0.000000
   glove100_10k          17        geometry_backbone_random     128               0.052784                                0.018807               0.062762              0.046765                               -0.001302
   glove100_10k          17 geometry_backbone_mpcc_shuffled     128               0.035837                                0.019718               0.047786              0.049909                                0.000000
   glove100_10k          29                      algorithm4     125               0.022865                                0.029298               0.020783              0.015237                               -0.002133
   glove100_10k          29                        geometry     125               0.021756                                0.014674               0.017085              0.000235                               -0.006133
   glove100_10k          29                    maxmin_angle     125               0.104697                                0.050631               0.096856              0.041586                               -0.000633
   glove100_10k          29              length_aware_angle     125               0.022865                                0.029298               0.020783              0.015237                               -0.002133
   glove100_10k          29                           ggr_0     125               0.046413                                0.022852               0.025575             -0.000454                               -0.004000
   glove100_10k          29        geometry_backbone_random     125               0.023879                                0.026631               0.024818              0.019068                                0.000000
   glove100_10k          29 geometry_backbone_mpcc_shuffled     125               0.028687                                0.016853               0.037009              0.025816                                0.000000
       sift_10k           7                      algorithm4     123               0.003643                                0.007243              -0.000438              0.002054                                0.000739
       sift_10k           7                        geometry     123              -0.036862                               -0.003516              -0.024882             -0.008878                               -0.001971
       sift_10k           7                    maxmin_angle     123               0.087610                                0.083214               0.099514              0.045650                                0.002288
       sift_10k           7              length_aware_angle     123               0.003643                                0.007243              -0.000438              0.002054                                0.000739
       sift_10k           7                           ggr_0     123              -0.035754                                0.030020              -0.029686             -0.007283                               -0.001971
       sift_10k           7        geometry_backbone_random     123               0.012078                                0.005807               0.003780              0.000734                                0.000739
       sift_10k           7 geometry_backbone_mpcc_shuffled     123               0.012934                                0.007243               0.004789              0.001626                                0.000739
       sift_10k          17                      algorithm4     122               0.012295                               -0.004098              -0.001561              0.004859                                0.000000
       sift_10k          17                        geometry     122               0.020062                                0.009953               0.006645              0.008372                                0.000000
       sift_10k          17                    maxmin_angle     122               0.179249                                0.099689               0.147276              0.071237                                0.000000
       sift_10k          17              length_aware_angle     122               0.012295                               -0.004098              -0.001561              0.004859                                0.000000
       sift_10k          17                           ggr_0     122               0.058177                                0.045199               0.045911              0.020863                                0.000000
       sift_10k          17        geometry_backbone_random     122               0.016393                                0.002049              -0.004554              0.001792                                0.000000
       sift_10k          17 geometry_backbone_mpcc_shuffled     122               0.016393                                0.002049              -0.005933              0.006226                                0.000000
       sift_10k          29                      algorithm4     137               0.002074                                0.000249               0.003027              0.000655                                0.000000
       sift_10k          29                        geometry     137              -0.031746                               -0.031876              -0.011378              0.001553                                0.000000
       sift_10k          29                    maxmin_angle     137               0.075091                                0.033285               0.097932              0.074138                                0.000000
       sift_10k          29              length_aware_angle     137               0.002074                                0.000249               0.003027              0.000655                                0.000000
       sift_10k          29                           ggr_0     137              -0.005535                               -0.028032               0.022465              0.027742                                0.000000
       sift_10k          29        geometry_backbone_random     137              -0.000994                               -0.002818               0.001825              0.002766                                0.000000
       sift_10k          29 geometry_backbone_mpcc_shuffled     137               0.002074                                0.000249               0.003548              0.003679                                0.000000
```

## Proxy calibration

```text
        dataset                        selector  events  spearman_proxy_vs_real_strict  mean_absolute_calibration_error  signed_proxy_minus_real
arxiv_nomic_10k                      algorithm4     440                       0.319171                         0.442729                 0.367949
arxiv_nomic_10k                        geometry     440                       0.253533                         0.465586                 0.392189
arxiv_nomic_10k          geometry_backbone_mpcc     440                       0.316638                         0.430458                 0.359417
arxiv_nomic_10k geometry_backbone_mpcc_shuffled     440                       0.297321                         0.448705                 0.374944
arxiv_nomic_10k        geometry_backbone_random     440                       0.314689                         0.440218                 0.365462
arxiv_nomic_10k                           ggr_0     440                       0.299616                         0.484558                 0.413637
arxiv_nomic_10k              length_aware_angle     440                       0.319171                         0.442729                 0.367949
arxiv_nomic_10k                    maxmin_angle     440                       0.240924                         0.523598                 0.453869
   glove100_10k                      algorithm4     384                       0.218696                         0.587373                 0.540984
   glove100_10k                        geometry     384                       0.198320                         0.580754                 0.527189
   glove100_10k          geometry_backbone_mpcc     384                       0.195705                         0.559940                 0.518576
   glove100_10k geometry_backbone_mpcc_shuffled     384                       0.207792                         0.576051                 0.527937
   glove100_10k        geometry_backbone_random     384                       0.219335                         0.585714                 0.539384
   glove100_10k                           ggr_0     384                       0.228048                         0.585152                 0.530738
   glove100_10k              length_aware_angle     384                       0.218696                         0.587373                 0.540984
   glove100_10k                    maxmin_angle     384                       0.156590                         0.631196                 0.583481
       sift_10k                      algorithm4     382                       0.262861                         0.506299                 0.465882
       sift_10k                        geometry     382                       0.244883                         0.488042                 0.438252
       sift_10k          geometry_backbone_mpcc     382                       0.285945                         0.502106                 0.463867
       sift_10k geometry_backbone_mpcc_shuffled     382                       0.271265                         0.510102                 0.470426
       sift_10k        geometry_backbone_random     382                       0.265327                         0.508831                 0.469196
       sift_10k                           ggr_0     382                       0.244557                         0.502717                 0.449829
       sift_10k              length_aware_angle     382                       0.262861                         0.506299                 0.465882
       sift_10k                    maxmin_angle     382                       0.238145                         0.574700                 0.526935
```

The final PASS/STOP label must be assigned only after checking the preregistered two-dataset, majority-seed, strong-baseline, and edge-length criteria together.
