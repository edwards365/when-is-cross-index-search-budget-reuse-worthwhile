# Information structure

`I_0` includes the source policy, source build, and metadata available before target labels. `I_m` may add fixed-random, stratified, or adaptive target sentinels; labeled or unlabeled fingerprints; checkpoint traces; and deployable target metadata. Every observation channel must state its sampling law and cost.

For adaptive evidence, at round `t` the rule chooses `Q_t=psi_t(H_{t-1})` and observes `Y_t`, where `H_{t-1}=(Q_1,Y_1,...,Q_{t-1},Y_{t-1})`. The transcript is `Z_m=(Q_1,Y_1,...,Q_m,Y_m)`. Its likelihood includes both the policy and conditional observation channel; iid KL tensorization is not used for adaptive probes.

`I_theta` contains the complete target response and is nondeployable. Any distance, margin, or cover using oracle safe budgets belongs to `I_theta` and cannot be treated as a deployment fingerprint.

Information refinement alone can only enlarge the feasible rule class when the action class and safety constraint are held fixed. Acquisition cost is accounted for separately, so more information may lower the decision component while increasing total cost.
