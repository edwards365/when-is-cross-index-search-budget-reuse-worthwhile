# E4.2 final hotfix report

Parent `6dce847f6102fa212f9eb1ef0b2e8bbae266a4af` replayed byte-identically. The old H1-A4 implementation was wrong because `state.nunique(axis=1)>1` included finite-budget differences. Correct mixed feasible/censored rates are SIFT 0.024000 and Arxiv 0.025333; all-feasible/all-censored counts are 732/0 and 730/1.

The jointly-feasible H1-B absolute differences are 22.526 and 14.417; H1-C values are 3.334 and 3.129. SIFT absolute/reference/increment risks are 0.223734/0.008000/0.215734; Arxiv values are 0.183761/0.012556/0.171205. Random-only and two-ended leave-one-seed/order risk increments and safe NDC taxes are all positive.

Seven event classes are mutually exclusive and complete; raw nonmonotonicity is a separate flag. Grid censoring is fully shown and cannot be promoted to true endpoint nonexistence. Deployment decisions are SIFT 19 certified candidates and 5 abstentions; Arxiv 16 certified candidates and 8 abstentions. No uncertified candidate or fallback is deployed. Status: `PARTIAL_TARGET_ABSTENTION_REQUIRED`. Scientific label `E4_H1_H2_TRANSPORT_CONFIRMED_REGISTERED_HNSWLIB_FAMILY`; deployment `NO_DEPLOYABLE_VALUE`; final `E4_FINAL_HOTFIX_PASS_FREEZE_HNSWLIB_EVIDENCE`.
