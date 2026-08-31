import fs from "node:fs";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = process.env.ICBA_CIBS_ROOT;
if (!root) throw new Error("ICBA_CIBS_ROOT is required");
const out = path.join(root, "results", "icba_cibs_lock");
fs.mkdirSync(out, { recursive: true });

function quote(v) {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

async function save(name, headers, rows) {
  const csv = [headers, ...rows].map(r => r.map(quote).join(",")).join("\n") + "\n";
  const wb = await Workbook.fromCSV(csv, { sheetName: "data" });
  const check = await wb.inspect({ kind: "table", range: `data!A1:${String.fromCharCode(64 + headers.length)}${rows.length + 1}`, include: "values", table_max_rows: Math.min(5, rows.length + 1), table_max_cols: headers.length });
  if (!check || !check.ndjson) throw new Error(`inspection failed for ${name}`);
  fs.writeFileSync(path.join(out, name), csv, "utf8");
}

await save("core_literature_matrix.csv",
  ["id","citation","year","venue","read_status","theorem_or_result_checked","proof_scope_checked","closest_cibs_component","missing_cibs_structure","overlap","official_url"], [
  ["L01","Wang, Wagenmaker & Jamieson, Best Arm Identification with Safety Constraints",2022,"AISTATS","LEVEL_A_FULLTEXT_PROOF_CHECKED","SafeBAI-Linear and SafeBAI-Monotonic guarantees","main statements and proof architecture","safety-constrained identification","not paired shared-query build-budget selection or service cost","STRONG_THEOREM_OVERLAP","https://proceedings.mlr.press/v151/wang22o.html"],
  ["L02","Garivier & Kaufmann, Optimal Best Arm Identification with Fixed Confidence",2016,"COLT","LEVEL_A_FULLTEXT_PROOF_CHECKED","Track-and-Stop lower bound and asymptotic optimality","main theorems and change-of-measure route","fixed-confidence best action","no simultaneous recall certificate or full-information query matrix","STRONG_THEOREM_OVERLAP","https://proceedings.mlr.press/v49/garivier16a.html"],
  ["L03","Kalyanakrishnan et al., PAC Subset Selection in Stochastic Multi-armed Bandits",2012,"ICML","LEVEL_A_FULLTEXT_PROOF_CHECKED","LUCB correctness and sample complexity","main theorem and confidence event proof","fixed-confidence elimination","bandit feedback; no build-service semantics","STRONG_THEOREM_OVERLAP","https://icml.cc/2012/papers/604.pdf"],
  ["L04","Angelopoulos et al., Learn then Test",2022,"ICLR","LEVEL_A_FULLTEXT_PROOF_CHECKED","FWER-valid calibration of fixed families","multiple-testing guarantees and proofs","simultaneous safe selection","no Graph-ANNS build action or offline cost","STRONG_THEOREM_OVERLAP","https://openreview.net/forum?id=TNVB5jLYpV"],
  ["L05","Bates et al., Distribution-Free, Risk-Controlling Prediction Sets",2021,"JACM","LEVEL_A_FULLTEXT_PROOF_CHECKED","holdout UCB risk control","definition and main risk theorem/proof","fixed-target risk UCB","no build portfolio or safe-set NDC selection","STRONG_THEOREM_OVERLAP","https://doi.org/10.1145/3478535"],
  ["L06","Angelopoulos et al., Conformal Risk Control",2024,"arXiv","LEVEL_A_FULLTEXT_PROOF_CHECKED","monotone expected-loss CRC guarantee","main statements and proofs","risk-control module","expectation/monotone loss differs from arbitrary raw-ef actions","PARTIAL_METHOD_OVERLAP","https://arxiv.org/abs/2208.02814"],
  ["L07","Li et al., Hyperband",2018,"JMLR","LEVEL_A_FULLTEXT_PROOF_CHECKED","successive-halving resource allocation","main algorithm and theoretical analysis","configuration racing","no safety certificate or endpoint event","PARTIAL_METHOD_OVERLAP","https://jmlr.org/papers/v18/16-558.html"],
  ["L08","Xu et al., SATzilla",2008,"JAIR","LEVEL_A_FULLTEXT_PROOF_CHECKED","portfolio-based per-instance selection","full method and empirical/statistical model sections","algorithm portfolios","no finite-sample recall-risk control","SYSTEMS_BASELINE_ONLY","https://doi.org/10.1613/jair.2490"],
  ["L09","Howard et al., Time-uniform Chernoff Bounds via Nonnegative Supermartingales",2020,"Probability Surveys","LEVEL_A_FULLTEXT_PROOF_CHECKED","anytime-valid confidence sequences","main theorems and supermartingale proofs","CIBS-Race inference","generic tool; no graph action or cost","STRONG_THEOREM_OVERLAP","https://doi.org/10.1214/18-PS321"],
  ["L10","Gupta, Joshi & Yağan, Best-Arm Identification in Correlated Multi-Armed Bandits",2021,"IEEE JSAIT","LEVEL_A_FULLTEXT_PROOF_CHECKED","C-LUCB guarantees","main theorems and pseudo-reward proof route","correlated candidate elimination","pseudo-rewards differ from observing every action on each query","ANALOGY_ONLY","https://doi.org/10.1109/JSAIT.2021.3076849"],
  ["L11","Wang et al., ANNiE: A Learned Query Cost Estimator for Graph-Based ANNS",2026,"PVLDB 19(11)","LEVEL_A_FULLTEXT_PROOF_CHECKED","query-cost and reliability target definitions","full method and relevant guarantee route","ANN query budgeting","fixed/index-specific learned model; no multi-build simultaneous certificate","PARTIAL_METHOD_OVERLAP","https://doi.org/10.14778/3836663.3836728"],
  ["L12","Horchidan et al., ConANN: Conformal Approximate Nearest Neighbor Search",2025,"PVLDB 19(1)","LEVEL_A_FULLTEXT_PROOF_CHECKED","conformal/CRC ANN risk control","full method and guarantee sections","ANN risk control","fixed IVF index; no build-budget portfolio accounting","PARTIAL_METHOD_OVERLAP","https://doi.org/10.14778/3772181.3772184"],
  ["L13","Bae et al., QBAT: Model-based Query Budget Autotuner for Clustering-based ANNS",2026,"PVLDB","FULLTEXT_UNVERIFIED","official program abstract only","no proof cleared this round","per-query ANN budget tuning","direct theorem/method boundary unresolved","FULLTEXT_UNVERIFIED","https://vldb.org/2026/"],
]);

await save("prior_art_crosswalk.csv",
  ["work","multiple_graph_builds","joint_build_budget_action","shared_target_truth","simultaneous_recall_risk","cost_selection_in_safe_set","full_offline_cost","independent_portfolios","direct_prior_trigger","overlap"], [
  ["Learn-Then-Test","NO","GENERIC_CONFIGURATION_ONLY","YES_GENERIC","YES","NO","NO","NO","NO","STRONG_THEOREM_OVERLAP"],
  ["RCPS","NO","NO","YES_GENERIC","SINGLE_OR_REGISTERED_RULE","NO","NO","NO","NO","STRONG_THEOREM_OVERLAP"],
  ["SafeBAI","NO","ARM_DOSE_ACTION","NO_PAIRED_FULL_INFORMATION","ADAPTIVE_SAFETY","YES_OBJECTIVE","NO","NO","NO","STRONG_THEOREM_OVERLAP"],
  ["Track-and-Stop/LUCB","NO","ARM_ONLY","NO","NO_SAFETY_CONSTRAINT","YES_OBJECTIVE","NO","NO","NO","STRONG_THEOREM_OVERLAP"],
  ["Hyperband","GENERIC_CONFIGS","GENERIC_RESOURCE","NO","NO","YES","RESOURCE_COST_ONLY","NO","NO","PARTIAL_METHOD_OVERLAP"],
  ["SATzilla","ALGORITHM_PORTFOLIO","PER_INSTANCE_ACTION","NO","NO","YES_PREDICTED","PARTIAL","BENCHMARK_INSTANCES","NO","SYSTEMS_BASELINE_ONLY"],
  ["ANNiE","SINGLE_FIXED_INDEX","QUERY_BUDGET_ONLY","TARGET_LABELS","NO_FAMILYWISE_CERTIFICATE","MODEL_OUTPUT","NO_MULTI_BUILD","NO","NO","PARTIAL_METHOD_OVERLAP"],
  ["ConANN","SINGLE_IVF_INDEX","QUERY/SEARCH_PARAMETER","CALIBRATION_TRUTH","RISK_CONTROL","NO_BUILD_SELECTION","NO_MULTI_BUILD","NO","NO","PARTIAL_METHOD_OVERLAP"],
  ["QBAT","UNVERIFIED","QUERY_BUDGET_MODEL","TARGET_WORKLOAD","UNVERIFIED","YES_TUNING","UNVERIFIED","UNVERIFIED","UNRESOLVED","FULLTEXT_UNVERIFIED"],
]);

await save("theorem_status.csv",
  ["theorem_id","title","status","classification","assumptions","guarantee","limitation"], [
  ["T-CIBS1","Fixed-family simultaneous safe selection","FORMAL_PROOF_COMPLETE","CLASSICAL_APPLICATION","frozen finite family; valid simultaneous UCBs; query sampling assumptions","P(r(a_hat)<=delta)>=1-alpha for any selected certified action","fallback needs separate safety basis"],
  ["T-CIBS2","Bonferroni exact-binomial instance","FORMAL_PROOF_COMPLETE","CLASSICAL_APPLICATION","iid Bernoulli failures per action across queries; M=KL","finite-sample family-wise risk control","may be conservative under dependence"],
  ["T-CIBS3","Cost near-optimality","FORMAL_PROOF_RESTRICTED","RESTRICTED_DOMAIN_PROPOSITION","simultaneous mean-cost concentration; comparison optimum is certified","2 eta_max regret to best certified action","ideal safe optimum comparison also needs its certification"],
  ["T-CIBS4","Paired full-information variance","CLASSICAL_APPLICATION","CLASSICAL_APPLICATION","finite second moments","Var(D)=Var(A)+Var(B)-2Cov(A,B)","no unconditional power dominance"],
  ["T-CIBS5","Build-service break-even","FORMAL_PROOF_COMPLETE","CLASSICAL_APPLICATION","consistent cost units; realized per-query gain g","N*=offline/g for g>0","mean conclusion says nothing about p95"],
  ["T-CIBS6","Fixed-candidate lower bound","FORMAL_PROOF_RESTRICTED","CLASSICAL_APPLICATION","two distinguishable joint observation laws; fixed confidence","Omega(log(1/beta)/gap^2) in regular Bernoulli/sub-Gaussian cases","classical specialization; constants/model dependent"],
  ["T-CIBS7","Fixed-target/open-world boundary","FORMAL_PROOF_COMPLETE","RESTRICTED_DOMAIN_PROPOSITION","only named-portfolio target-query data","certificate limited to named portfolio and P_Q","outer-build claim needs extra build distribution/units"],
]);

await save("cp_failure_thresholds.csv",
  ["setting","K","L","M","n","alpha","delta","alpha_per_action","max_certifiable_failures","ucb_at_max","ucb_at_next","zero_failure_ucb","zero_failure_min_n","method"], [
  ["main",3,12,36,256,0.05,0.05,0.001388888888888889,3,0.04847011813277262,0.05494821081357332,0.025372760986095606,129,"one-sided Clopper-Pearson plus Bonferroni"],
  ["low_cost",2,12,24,128,0.05,0.05,0.0020833333333333333,0,0.04708798510235187,0.06387989996404543,0.04708798510235187,121,"one-sided Clopper-Pearson plus Bonferroni"],
  ["alternate_if_only_250_sentinel",3,12,36,250,0.05,0.05,0.001388888888888889,3,0.04961098680203266,0.05622713402593215,0.02597373038696847,129,"one-sided Clopper-Pearson plus Bonferroni"],
]);

await save("counterexample_results.csv",
  ["counterexample_id","name","finite_witness","verified_quantity","expected_failure","test_status"], [
  ["CE01","Per-action coverage is not family-wise","M=36 independent 5% errors",0.841958,"post-selection family error exceeds 5%","PASS"],
  ["CE02","Mean recall does not control failure risk","94 perfect and 6 zero-recall queries",0.06,"mean .94 but event risk .06","PASS"],
  ["CE03","Raw ef need not be monotone","recall 1.0 at ef40 and .9 at ef80",-0.1,"larger ef has lower raw recall","PASS"],
  ["CE04","Budget proxy can reverse NDC","ef20/NDC100 vs ef40/NDC80",20,"lower ef has worse NDC","PASS"],
  ["CE05","Mean gain can worsen p95","A:94x0+6x100; B:100x7",-1,"A mean lower and tail worse","PASS"],
  ["CE06","Sentinel/evaluation reversal","sentinel A1/B2; evaluation A3/B2",2,"selected winner reverses","PASS"],
  ["CE07","Post-hoc candidate invalidates certificate","20 unadjusted 95% intervals",0.641514,"family error exceeds 5%","PASS"],
  ["CE08","Empty safe set cannot force choice","UCB .08,.09 with delta .05",0,"no certified action","PASS"],
  ["CE09","Endpoint imputation hides failures","10 of 100 endpoints unreachable",0.1,"true failure rate exceeds delta","PASS"],
  ["CE10","Shared truth is not free search","truth100 plus 36 searches x10",460,"search cost omitted by shortcut","PASS"],
  ["CE11","Query bootstrap misses portfolio reversal","P1 prefers A; P2 prefers B",1,"outer-build conclusion fails","PASS"],
  ["CE12","No finite break-even when g<=0","offline1000 and g=-.1","INF","no finite N","PASS"],
  ["CE13","Negative covariance hurts pairing","varA=varB=1,cov=-.5",3,"paired variance exceeds independent 2","PASS"],
  ["CE14","Bonferroni can be conservative","36 perfectly correlated tests",0.00138889,"effective family error need not scale by 36","PASS"],
]);

await save("semantic_field_contract.csv",
  ["field","type","role","allowed_source","frozen_before","semantics","forbidden_use"], [
  ["build_id","string","action","build manifest","sentinel access","immutable serialized build identity","post-hoc seed selection"],
  ["build_seed","integer","generation","preregistration","sentinel access","legal random seed","outcome-driven generation"],
  ["insertion_order_sha256","hex","generation","preregistration","sentinel access","exact insertion-order identity","silent reorder"],
  ["raw_fixed_ef","integer","action","preregistered grid","sentinel access","global raw search setting; not expansion cap","monotone-envelope relabeling"],
  ["query_role","enum","sampling","role manifest","truth access","sentinel/evaluation/future_confirm/design","role overlap or borrowing"],
  ["query_sha256","hex","sampling","role manifest","truth access","hash of ordered query IDs","untracked mutation"],
  ["failure","boolean","risk","raw recall and endpoint status","analysis","1 iff recall<tau or endpoint infeasible","max-ef success imputation"],
  ["risk_ucb","float","certificate","sentinel only","selection","simultaneous one-sided UCB","evaluation-driven tuning"],
  ["mean_ndc","float","primary cost","candidate searches","selection","mean actual distance computations","budget proxy substitution"],
  ["p95_ndc","float","tail gate","candidate searches/evaluation","tie-break rule frozen","separate tail statistic","weighted mean hiding"],
  ["truth_cost","float","offline cost","accounting log","analysis plan","incremental exact-truth acquisition","multiply by K without reason"],
  ["candidate_search_cost","float","offline cost","action execution log","analysis plan","all evaluated action searches","omit because truth shared"],
  ["fallback","string","deployment","preregistration","sentinel access","external fixed-safe action","forced unsafe candidate"],
]);

await save("pilot_gate_table.csv",
  ["gate_id","scope","metric","pass_condition","stop_condition","evidence_role","status_before_pilot"], [
  ["G_RECALL","both datasets","Recall@10 delta",">=-0.001","below -0.001","evaluation","UNMEASURED"],
  ["G_MEAN_NDC","both datasets","net mean NDC gain",">=1%","proxy does not translate or gain <1%","evaluation plus offline accounting","UNMEASURED"],
  ["G_P95","both datasets","p95 NDC delta","<=0",">0","evaluation","UNMEASURED"],
  ["G_SAFETY","both datasets","unsafe selected","controlled at registered alpha","certificate failure","sentinel and independent evaluation","UNMEASURED"],
  ["G_ENDPOINT","both datasets","endpoint failure","not worse","worsens","evaluation","UNMEASURED"],
  ["G_BREAK_EVEN","both datasets","workload N*","finite","g<=0 or infeasible workload","offline logs plus evaluation","UNMEASURED"],
  ["G_ROBUSTNESS","both datasets","top-1% deletion gain",">0","<=0","evaluation","UNMEASURED"],
  ["G_PORTFOLIO","both datasets","single-build dominance","not dominated by one selected seed","one build drives result","independent portfolio","UNMEASURED"],
  ["G_MULTIPLICITY","both datasets","certified set availability","usable","all rejected/unusable","sentinel","UNMEASURED"],
  ["G_ROLES","global","pairwise overlap","0","any overlap or truth contamination","role manifest","REQUIRED_BEFORE_RUN"],
  ["G_REPLAY","global","artifact hash replay","exact","any artifact cannot replay","artifact manifest","REQUIRED_BEFORE_RUN"],
]);

console.log("created 7 inspected CSV artifacts");
