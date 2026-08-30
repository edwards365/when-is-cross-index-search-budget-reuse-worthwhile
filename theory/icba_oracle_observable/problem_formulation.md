# Oracle–observable recovery problem

## Two decision layers

The inner decision chooses an ordered search budget for each query. The outer decision chooses how a rebuilt target index is handled: reuse, recalibrate, retrain, or fallback. Full target response is available only to the oracle comparator.

Define recall failure

`Z_rec(q,b,theta)=1{Recall_theta(q,b)<tau}`.

Define `Z_abs` to equal one for recall failure, endpoint infeasibility, or any other preregistered absolute deployment failure. Ordinary under-budget, right censoring, and no-safe-endpoint are recorded separately even though the latter two enter `Z_abs`.

## Decision value

For an information sigma-field `I`,

`R_{delta,N}(I)=inf_{pi in Pi(I)} E_theta[C_N(theta,pi)]`

subject to exactly one declared safety semantics. Define

- `R_0=R_{delta,N}(I_0)`;
- `R_m=R_{delta,N}(I_m)`;
- `R_theta=R_{delta,N}(I_theta)`;
- oracle headroom `H_oracle=R_0-R_theta`;
- observable value `H_obs(m)=R_0-R_m`;
- identification gap `G_id(m)=R_m-R_theta`.

The framework distinguishes opportunity from recoverability: `H_oracle>0` says environment-conditioned action can help; only `H_obs(m)>0` says deployable evidence has positive decision value.

## Scope

The formal positive results are fixed-target unless an iid/exchangeable `Pi` and build-level sample are explicitly supplied. Frozen headroom estimates are empirical witnesses, never assumptions of a theorem. No result below labels a method confirmatory or deployable.
