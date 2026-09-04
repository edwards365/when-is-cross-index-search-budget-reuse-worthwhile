import fs from "node:fs";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = process.env.ICBA_GSC_ROOT;
if (!root) throw new Error("ICBA_GSC_ROOT is required");
const out = path.join(root, "results", "icba_gsc_theory_delta");
fs.mkdirSync(out, { recursive: true });

function q(v) {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
async function save(name, headers, rows) {
  const csv = [headers, ...rows].map(r => r.map(q).join(",")).join("\n") + "\n";
  const wb = await Workbook.fromCSV(csv, { sheetName: "data" });
  const cols = headers.length <= 26 ? String.fromCharCode(64 + headers.length) : "Z";
  const inspected = await wb.inspect({ kind: "table", range: `data!A1:${cols}${rows.length + 1}`, include: "values", tableMaxRows: Math.min(4, rows.length + 1), tableMaxCols: Math.min(headers.length, 12) });
  if (!inspected || !inspected.ndjson) throw new Error(`artifact inspection failed: ${name}`);
  fs.writeFileSync(path.join(out, name), csv, "utf8");
}

await save("conflict_ledger.csv",
  ["conflict_id","concept","earlier_statement","earlier_source","corrected_statement","authoritative_source","correction_reason","current_status","allowed_paper_wording","prohibited_wording"], [
  ["C01","raw ef vs actual expansion","ef can stand for expansion budget","early ordered-rung drafts","raw ef is an independent search-control action; expansions/NDC are measured outcomes","904de537; b0190169","implementation semantics and nonmonotone response","SUPERSEDED_BY_SEMANTIC_REAUDIT","raw fixed-ef action with separately reported expansions/NDC","ef is an expansion or NDC cap"],
  ["C02","B_G^ef vs B_G^exp","same ordered budget object","early theory notes","distinct estimands; connect only with a proved implementation map","904de537","no deterministic ef-to-prefix map assumed","VALID_WITH_RESTRICTED_SCOPE","expansion-prefix result is restricted","T-SC5 applies directly to raw ef"],
  ["C03","native Recall monotonicity","larger ef guarantees no lower Recall","ordered-rung draft","each raw fixed-ef action is separately certified","904de537","independent runs and graph search effects","EMPIRICALLY_REFUTED","report per-action recall and risk","fixed-ef Recall is query-wise monotone"],
  ["C04","expansion-prefix upward closure","prefix closure applies to all budgets","stable-build draft","only fixed implementation, observable trace, and margin assumptions","dca81b23; f7f08ce1","raw ef does not identify a prefix","VALID_WITH_RESTRICTED_SCOPE","conditional expansion-prefix proposition","prefix proof certifies raw ef"],
  ["C05","stage/NDC as ordered rung","stage is a safe budget ladder","T-SC drafts","stage is a candidate descriptor; NDC is a measured cost","904de537","control and outcome were conflated","SUPERSEDED_BY_SEMANTIC_REAUDIT","use stage only as metadata","stage family has nested failures"],
  ["C06","edge overlap to budget stability","structural similarity implies stable response","stable-build proposals","edge/trace similarity is not a risk or cost certificate","dca81b23","counterexamples with endpoint changes","THEORY_UNREFUTED_OPERATOR_FAILED","measure D_Z and D_C directly","edge Jaccard guarantees safety"],
  ["C07","high AUROC","high AUROC gives safe stopping threshold","operator reports","AUROC is association; threshold safety needs calibrated risk bound","41a44bd; b0190169","ranking is not calibration","VALID_WITH_RESTRICTED_SCOPE","AUROC is descriptive","AUROC certifies risk"],
  ["C08","paired B2 gains","paired query gain is deployment evidence","CFSR/CIBS drafts","paired estimates are efficiency diagnostics; disjoint evaluation is required","7417147; 736c3799","query-role and protocol issues","CONDITIONAL_REPRODUCTION_ONLY","paired result under declared role","paired gain proves independent benefit"],
  ["C09","CIBS candidate feasibility","CIBS proxy gains imply feasible pool","CIBS opportunity audit","latest closure has no two-dataset CI-supported joint-feasible action","736c3799","joint gates and recall slack","EMPIRICALLY_REFUTED","CIBS remains a baseline/negative control","CIBS already has deployable candidates"],
  ["C10","Stable-by-Construction","one failed operator invalidates stabilization","CFSR-Lite interpretation","operator failure narrows the tested family only","7417147; dca81b23","failure is family-specific","VALID_WITH_RESTRICTED_SCOPE","tested operator family failed","all stabilization is impossible"],
  ["C11","Active-RACS vs BAI","active sensing is novel theory","active recovery drafts","active sensing is a classical template; Graph-ANNS channel is the application","naghshvar2013; garivier2016","same change-of-measure structure","INHERITED_VALID","application-specific observation channel","new generic active-testing theorem"],
  ["C12","fixed-target vs open-world","query certificate transfers to unseen builds","open-world theory","certificate covers named portfolio and P_Q only","a9f88bbc; 41a44bd","missing outer build law","SUPERSEDED_BY_SEMANTIC_REAUDIT","fixed-target conditional safety","open-world safety solved"],
  ["C13","query bootstrap vs build bootstrap","query bootstrap covers portfolio","active observation gate","query bootstrap is within-portfolio; build-cluster is outer uncertainty","97ca42a; a9f88bbc","different sampling unit","VALID_WITH_RESTRICTED_SCOPE","state bootstrap unit explicitly","query bootstrap certifies open-world"],
  ["C14","Oracle headroom vs gain","oracle gap is method gain","joint closure summaries","oracle headroom is nondeployable upper bound","4e728d; 736c3799","oracle uses unavailable outcomes","ORACLE_ONLY","report as upper bound","oracle headroom is deployment gain"],
  ["C15","candidate selection vs attainability","correct selector guarantees a good candidate","GSC proposal","selection is conditional on candidate pool containing a feasible action","736c3799; GSC delta","empty or unsafe generated pool","NOT_ESTIMABLE","conditional small-closure theorem","GSC always generates a feasible action"],
]);

await save("theory_inheritance_matrix.csv",
  ["gsc_component","required_claim","inherited_theorem","source_commit","theorem_status","direct_inheritance_or_adaptation","assumptions","guarantee_object","empirical_dependency","novelty_level","proof_update_needed","allowed_claim"], [
  ["Generate","adaptive finite candidate proposals","finite candidate certification","41a44bd; b0190169","FORMAL_PROOF_COMPLETE","adaptation by sample split","final family frozen before certification","risk of final named actions","candidate generation quality","NEW_COMBINATION_OF_CLASSICAL_RESULTS","state generation sigma-field","adaptive generation can precede independent certification"],
  ["Generate","hidden build environment","Oracle-Observable gap","4e728d","FORMAL_PROOF_COMPLETE","direct inheritance","latent build can alter response","observable vs oracle action","operator features","INHERITED_VALID","none for fixed scope","build is a hidden condition variable"],
  ["Stabilize","reduce response dispersion","none; event-disagreement identity only","GSC delta","FORMAL_PROOF_RESTRICTED","new diagnostic object","same P_Q and endpoint semantics","D_Z/D_C and disagreement","must measure each separately","NEW_COMBINATION_OF_CLASSICAL_RESULTS","no structure-to-raw-ef bridge","stability is an empirical/conditional objective"],
  ["Stabilize","trace repair preserves response","expansion-prefix restricted proposition","dca81b23; f7f08ce1","FORMAL_PROOF_RESTRICTED","restricted adaptation","priority margin; fixed implementation; observable trace","expansion-prefix behavior","operator-specific","NEW_COMBINATION_OF_CLASSICAL_RESULTS","prove map or keep empirical","conditional trace statement only"],
  ["Stabilize","budget-response objective","T-CIBS4 paired cost identity","b0190169","CLASSICAL_APPLICATION","reuse cost identity","finite second moments; paired query","mean cost comparison","covariance and search cost","CLASSICAL_APPLICATION","none","paired estimates may improve efficiency"],
  ["Certify","fixed-target safety","T-CIBS1/T-CIBS2; LTT/RCPS","41a44bd; b0190169","FORMAL_PROOF_COMPLETE","direct inheritance","independent sample; frozen family","named build×raw-ef target risk","query sampling","CLASSICAL_APPLICATION","none","fixed-target simultaneous safety"],
  ["Certify","fallback safety","T-CIBS5/T-CIBS7","41a44bd; b0190169","FORMAL_PROOF_COMPLETE","direct inheritance","fallback has own safety basis","conditional deployment and cost","fallback cost","CLASSICAL_APPLICATION","state scope","fallback if all candidates fail"],
  ["Whole pipeline","positive net benefit","break-even identity","41a44bd; b0190169","FORMAL_PROOF_COMPLETE","new service composition","realized online gain and measured costs","service total cost","truth/build/operator cost","NEW_COMBINATION_OF_CLASSICAL_RESULTS","measure costs","conditional break-even only"],
]);

await save("theorem_status.csv",
  ["theorem_id","formal_title","status","classification","quantifiers_and_scope","assumptions","proof_summary","counterexample_or_boundary","fixed_target_scope","open_world_scope","observable_fields","allowed_claim","prohibited_claim"], [
  ["T-GSC1","Adaptive Generation with Independent Certification","FORMAL_PROOF_COMPLETE","CLASSICAL_CONDITIONAL_INFERENCE_APPLICATION","for every generation sigma-field realization; every frozen family of size <=M; probability >=1-alpha","generation/validation independent of certification; final family frozen; events fixed","condition on generation field, apply simultaneous bound, integrate by tower property","post-certification candidate modification breaks conditioning","valid for named target queries and final family","not implied","candidate manifest; certification IDs; alpha/M","adaptive pre-search followed by independent certification is safe","new adaptive inference theory"],
  ["T-GSC2","Baseline Inclusion and Safe Fallback","FORMAL_PROOF_COMPLETE","CLASSICAL_APPLICATION","for every candidate outcome, fallback if certified set empty","baseline has its own valid safety event","union/intersection of baseline and candidate certificate events","safe baseline does not imply NDC/p95 improvement","conditional safety","not implied","baseline certificate; fallback cost","fallback preserves declared safety","baseline inclusion guarantees gain"],
  ["T-GSC3","Certifiability Margin and Acceptance Probability","FORMAL_PROOF_COMPLETE","CLASSICAL_APPLICATION","for fixed action with r<=delta-gamma and finite M","Bernoulli query failures; valid CP/Hoeffding/KL bounds","concentration radius and CP zero-failure inversion","safe action can be rejected near boundary","fixed target","not implied","failure count; n; M; alpha; delta","margin controls sufficient sample order","exact characteristic time or universal power dominance"],
  ["T-GSC4","Positive Net-Benefit Condition","FORMAL_PROOF_COMPLETE","NEW_COMBINATION_OF_CLASSICAL_RESULTS","for realized costs and workload N","declared units; measured online/fallback/control/offline costs","algebraic subtraction and break-even rearrangement","positive oracle headroom can still yield negative deployment value","declared service scope","not implied","cost logs; workload; fallback rate","conditional positive net-benefit rule","oracle gain proves deployment gain"],
  ["T-GSC5","Behavioral Stability and Transfer-Risk Relation","FORMAL_PROOF_RESTRICTED","IDENTITY_OR_RESTRICTED_PROPOSITION","for fixed G,G',e and common P_Q; structural result only under explicit trace assumptions","same endpoint event; disagreement estimable; optional priority margin","event inclusion gives |r-r'|<=P(disagreement); trace layer requires extra assumptions","D_C, edge overlap, rank stability do not control D_Z generally","fixed target only","no open-world transfer","D_Z,D_C,endpoint,rank,trace","disagreement bound as restricted proposition","structure guarantees raw-ef safety"],
  ["T-GSC6","Finite Adaptive Candidate Search and Generalization","FORMAL_PROOF_COMPLETE","CLASSICAL_CONDITIONAL_INFERENCE_APPLICATION","for <=24 trials and <=3 generations with final freeze","finite registered search; independent certification; one final evaluation","sample splitting and finite-family simultaneous control","multiple evaluation tracks require extra adjustment","registered family","not implied","operator registry; family size; split IDs","independent certification absorbs pre-certification adaptivity","Hyperband/BAI theorem is new GSC theory"],
  ["T-GSC7","Conditional Small-Closure Theorem","FORMAL_PROOF_COMPLETE","RESTRICTED_DOMAIN_PROPOSITION","if generated candidate has margin, gain, noninferiority, valid certificate, N>N*","candidate attainability assumed; metric gates valid","intersect safety, metric and cost events","does not prove generator produces candidate","registered track only","not implied","candidate certificate; metric CI; costs","conditional Pareto improvement","GSC necessarily creates Pareto point"],
  ["T-GSC8","Environment Control versus Environment Inference","FORMAL_PROOF_RESTRICTED","RESTRICTED_DOMAIN_PROPOSITION","for controlled class in which response set is narrowed; otherwise indistinguishable worlds remain","control changes class/channel; latent alternatives defined","if all controlled environments share action, inference is unnecessary; otherwise lower bound remains","no identification-free open-world theorem","closed registered class","not implied","operator parameters; response set","control and inference are distinct routes","GSC abolishes hidden-environment lower bounds"],
]);

await save("counterexamples.csv",
  ["counterexample_id","category","finite_construction","quantity","expected_failure","formal_consequence","status"], [
  ["CE01","edge-to-endpoint","100 edges; two graphs share 99 but one altered bridge makes endpoint infeasible",0.99,"high Jaccard but endpoint state flips","edge overlap does not control Z","VERIFIED"],
  ["CE02","D_C_vs_D_Z","C=10 for every query/build; one build has Z=1 on one query",0,"D_C=0 while D_Z>0","cost dispersion alone cannot certify risk","VERIFIED"],
  ["CE03","average-vs-maximum","n=1000; one query changes from safe to failed",0.001,"mean disagreement .001 but maximum query risk 1","average response misses tail query","VERIFIED"],
  ["CE04","mean-p95","A:94 zeros+6 hundreds; B:100 sevens",-1,"A mean 6<7 but p95 100>7","mean gain does not imply tail gain","VERIFIED"],
  ["CE05","p95-vs-recall","A p95 improves but 10/100 queries fall below tau; B has no failures",10,"tail pass with hard recall failure","metrics need separate gates","VERIFIED"],
  ["CE06","zero-margin","r=delta and CP threshold near boundary",0,"acceptance probability is not guaranteed high","gamma>0 is needed for power","VERIFIED"],
  ["CE07","fallback-tax","online gain 1; rejection .2; fallback gap 8; control 0",-0.6,"1-.2*8<0","oracle/online gain can be net negative","VERIFIED"],
  ["CE08","baseline-inclusion","baseline r=.01; candidate r=.20 selected outside family event",0.19,"safe baseline does not rescue invalid candidate selection","baseline must be in valid simultaneous event","VERIFIED"],
  ["CE09","adaptive-certification","20 unadjusted 95% tests; choose minimum observed risk",0.641514,"family error 1-.95^20","post-certification selection breaks 95% claim","VERIFIED"],
  ["CE10","raw-ef","recall ef40=1.0; ef80=.9 on same query",-0.1,"larger raw ef lowers recall","no raw-ef monotone envelope","VERIFIED"],
  ["CE11","prefix-vs-ef","prefix expansions monotone but ef maps to different seeds/order",1,"prefix theorem does not identify raw ef behavior","expansion theorem cannot be relabeled","VERIFIED"],
  ["CE12","empty-pool","all generated candidates have UCB>.05",0,"selector forced to choose unsafe action","fallback is required","VERIFIED"],
  ["CE13","stability-cost","D_C decreases by 50%; operator cost=1000; online gain=.1/query",-999.9,"cost shrink does not pay operator cost","stability objective not service value","VERIFIED"],
  ["CE14","cross-dataset","dataset A gain +2%, dataset B gain -2%",-2,"one track passes, other violates tolerance","joint claim needs intersection gate","VERIFIED"],
  ["CE15","multi-track-selection","10 tracks each with 95% valid evaluation result",0.401263,"post-selection error 1-.95^10","fresh holdout/adjustment required","VERIFIED"],
  ["CE16","query-vs-build-bootstrap","within-build query SE=.01; two-build means reverse sign",1,"query CI significant but build cluster not","sampling unit mismatch","VERIFIED"],
]);

await save("prior_art_matrix.csv",
  ["id","work","year","domain","read_level","theorem_or_result_checked","graph_build_control","budget_response","risk_safety","independent_target_certification","full_cost_fallback","single_deployable_index","direct_seven_condition_prior","overlap","url"], [
  ["P01","HNSW: Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs",2018,"Graph-ANNS","LEVEL_A_FULLTEXT","construction/search description; no GSC theorem","yes","query ef/search","no distribution-free certificate","no","build/search cost empirical","yes","NO","PARTIAL_COMPONENT_OVERLAP","https://arxiv.org/abs/1603.09320"],
  ["P02","Fast Approximate Nearest Neighbor Search With The Navigating Spreading-out Graph",2019,"Graph-ANNS","LEVEL_A_FULLTEXT","NSG construction and search analysis","yes","search parameter","no","no","empirical","yes","NO","PARTIAL_COMPONENT_OVERLAP","https://doi.org/10.1109/TPAMI.2018.2888712"],
  ["P03","DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node",2019,"Graph-ANNS","LEVEL_A_FULLTEXT","Vamana/DiskANN construction and recall analysis","yes","search beam","no","no","system cost","yes","NO","PARTIAL_COMPONENT_OVERLAP","https://proceedings.neurips.cc/paper/2019/hash/098d86fbf3925c8f30e24dcbf0a8d9f8-Abstract.html"],
  ["P04","FreshDiskANN: A Fast and Accurate Graph-Based ANN Index for Streaming Similarity Search",2024,"Graph-ANNS","LEVEL_A_FULLTEXT","fresh construction and update method","yes","query search parameter","no","no","build/update cost","yes","NO","PARTIAL_COMPONENT_OVERLAP","https://arxiv.org/abs/2405.14358"],
  ["P05","Graph-Based Approximate Nearest Neighbor Search: A Review",2021,"Graph-ANNS","LEVEL_A_FULLTEXT","construction/search taxonomy","descriptive","search controls","no","no","empirical","yes","NO","ANALOGY_ONLY","https://doi.org/10.1145/3439951"],
  ["P06","Steiner-Hardness: A Query Hardness Measure for Graph-Based ANN Indexes",2024,"Graph-ANNS","LEVEL_A_FULLTEXT","hardness/structure metric","no direct control","query hardness","no","no","empirical","yes","NO","PARTIAL_COMPONENT_OVERLAP","https://doi.org/10.14778/3704965.3704974"],
  ["P07","MARGO: A Graph-Based Approximate Nearest Neighbor Index with Query-Aware Construction",2025,"Graph-ANNS","LEVEL_A_FULLTEXT","query-aware graph construction","yes","query-aware search","no finite certificate","no","construction cost empirical","yes","NO","STRONG_COMPONENT_OVERLAP","https://dl.acm.org/doi/10.1145/3725300"],
  ["P08","ANNiE: A Learned Query Cost Estimator for Graph-Based ANNS",2026,"ANN budgeting","LEVEL_A_FULLTEXT","Definition 5; Theorem 1; Corollary 1","fixed index","per-query cost budget","population/conditional statement","no","query cost; no fallback frontier","yes","NO","STRONG_COMPONENT_OVERLAP","https://doi.org/10.14778/3836663.3836728"],
  ["P09","QBAT: Model-based Query Budget Autotuner for Clustering-based ANNS",2026,"ANN budgeting","LEVEL_A_FULLTEXT","full method sections; no formal theorem","fixed/reprofiled index","per-query budget","empirical","no","profiling/search cost","yes","NO","STRONG_COMPONENT_OVERLAP","https://doi.org/10.14778/3836663.3836675"],
  ["P10","Distribution-Aware Exploration for Adaptive HNSW Search (Ada-ef)",2026,"ANN budgeting","LEVEL_A_FULLTEXT","adaptive HNSW exploration/statistical calibration","fixed index","per-query ef","empirical/CLT-style","no","search cost","yes","NO","STRONG_COMPONENT_OVERLAP","https://arxiv.org/abs/2512.06636"],
  ["P11","DARTH+: Approximate Nearest Neighbor Search with Declarative Recall and Quality Guarantees",2026,"ANN risk control","LEVEL_A_FULLTEXT","quality/termination guarantee route","fixed index","early stopping","conditional/empirical","no","search cost","yes","NO","STRONG_COMPONENT_OVERLAP","https://hal.science/hal-05566027v1"],
  ["P12","ConANN: Conformal Approximate Nearest Neighbor Search",2025,"ANN risk control","LEVEL_A_FULLTEXT","conformal/CRC guarantee","fixed IVF index","query probe budget","target calibration","yes calibration","no build portfolio cost","yes","NO","STRONG_COMPONENT_OVERLAP","https://doi.org/10.14778/3772181.3772184"],
  ["P13","Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control",2025,"Risk control","LEVEL_A_FULLTEXT","Theorem 1; finite candidate FWER","generic predictors","candidate selection","yes","yes holdout","no Graph-ANNS service cost","not applicable","NO","STRONG_THEOREM_OVERLAP","https://doi.org/10.1214/24-AOAS1998"],
  ["P14","Best Arm Identification with Safety Constraints",2022,"Safe selection","LEVEL_A_FULLTEXT","Theorems 1-3; safe exploration","arms/doses","adaptive allocation","yes safety constraint","no build layer","sampling cost","no","NO","STRONG_THEOREM_OVERLAP","https://proceedings.mlr.press/v151/wang22o.html"],
  ["P15","Active Sequential Hypothesis Testing",2013,"Active testing","LEVEL_A_FULLTEXT","Theorems 1-3; controlled sensing/stopping","latent hypotheses","adaptive sensing","error/sample-cost tradeoff","target observations","sample cost and decision loss","not applicable","NO","STRONG_THEOREM_OVERLAP","https://doi.org/10.1214/13-AOS1144"],
]);

await save("operator_overlap_matrix.csv",
  ["operator_id","operator","closest_prior_1","closest_prior_2","closest_prior_3","same_input","same_operation","same_objective","same_guarantee","same_cost_model","main_difference","retained_innovation","required_citation","overlap_level","claim_limit"], [
  ["O1","deterministic construction","HNSW","NSG","DiskANN/Vamana","dataset and graph","reproducible build","stability/replay","no prior safety","build cost","GSC binds it to response diagnostics","reproducibility condition","HNSW; NSG; DiskANN","STRONG_COMPONENT_OVERLAP","not first deterministic/stable Graph-ANNS"],
  ["O2","trace-guided bridge overlay","MARGO","Steiner-Hardness","Graph-Based ANNS Revisited","graph/query traces","bridge/edge repair","navigation response","none","construction cost","response-targeted trace proposal","conditional Graph-ANNS combination","MARGO; Steiner-Hardness","PARTIAL_MECHANISM_OVERLAP","not structure-to-raw-ef theorem"],
  ["O3","budget-response local repair","ANNiE","QBAT","DARTH+","queries, response labels","local graph repair","cost/recall response","fixed-index or empirical","search/profiling","acts at construction time","potential construction-specific combination","ANNiE; QBAT; DARTH+","STRONG_COMPONENT_OVERLAP","no prior-free budget claim"],
  ["O4","response-weighted robust pruning","NSG","Vamana","FreshDiskANN","graph/search statistics","pruning","robust response","none","build/search","weights response rather than geometry only","potential operator result","NSG; DiskANN; FreshDiskANN","DOMAIN_SPECIFIC_NEW_COMBINATION","only after independent evaluation"],
  ["O5","multi-build consensus","SATzilla","correlated BAI","CIBS","candidate portfolio","aggregate/compare","safe-cost choice","generic or classical","evaluation cost","one build deployed; consensus diagnostic","portfolio-aware Graph-ANNS package","SATzilla; SafeBAI; CIBS","PARTIAL_MECHANISM_OVERLAP","not new portfolio theory"],
  ["O6","response-aware insertion schedule","HNSW insertion sensitivity","FreshDiskANN","workload-aware indexing","build order and workload","reorder insertion","response stability","none","build cost","independent target certification","possible build-control combination","HNSW; FreshDiskANN","DOMAIN_SPECIFIC_NEW_COMBINATION","not insertion-order safety theorem"],
  ["O7","two-operator combination","O2","O3","O4/O6","union of above","composed repair","response stability and cost","only GSC certificate after freeze","full service cost","composed pipeline with split evidence","conditional method package","all component citations","DOMAIN_SPECIFIC_NEW_COMBINATION","no pre-experiment contribution claim"],
]);

await save("assumption_observability.csv",
  ["assumption_id","assumption","theorem_or_module","classification","observable_field_or_test","required_scope","failure_interpretation","current_status"], [
  ["A01","final candidate family frozen before certification","T-GSC1","design-only","manifest timestamp and hash","registered finite family","adaptive validity fails if modified after certificate views","REQUIRED"],
  ["A02","certification sample independent of generation/validation","T-GSC1","certification-only","role IDs and split hash; no overlap","target query distribution","certificate invalid if reused adaptively","REQUIRED"],
  ["A03","endpoint-aware failure semantics fixed","all risk theorems","directly observable","raw recall and endpoint status","same tau across actions","imputation can hide failures","REQUIRED"],
  ["A04","candidate count M and alpha ledger fixed","T-GSC1/T-GSC3","design-only","operator registry and alpha record","finite search","unregistered tracks inflate error","REQUIRED"],
  ["A05","positive safety margin gamma","T-GSC3","certification-only","estimated margin with independent uncertainty","fixed target","safe candidate may be rejected","NOT_ESTIMABLE_BEFORE_CERTIFICATION"],
  ["A06","D_Z measured separately from D_C","T-GSC5","approximately testable","per-query response matrix","same P_Q","D_C reduction cannot be interpreted as risk reduction","REQUIRED"],
  ["A07","priority margin for trace repair","T-GSC5 structural layer","approximately testable","frontier score gap and trace fields","fixed implementation","without margin no prefix claim","DESIGN_REQUIRED"],
  ["A08","raw ef-to-expansion map","T-GSC5 structural layer","not estimable without new proof","paired trace experiment cannot certify globally","raw ef claim","prefix result cannot transfer","NOT_ASSUMED"],
  ["A09","candidate generator attains good action","T-GSC7","not estimable in theory alone","independent candidate-pool evaluation","registered track","conditional theorem has no force if pool empty","EMPIRICAL_ONLY"],
  ["A10","online gain G_online positive","T-GSC4","directly observable","mean NDC and wall-clock logs","declared workload","D<=0 means no break-even","UNMEASURED"],
  ["A11","fallback gap and rejection probability measured","T-GSC4","directly observable","fallback/action logs","service workload","fallback tax can erase gain","UNMEASURED"],
  ["A12","outer build support/exchangeability","open-world extension","not estimable","independent build clusters","open-world claim","fixed-target certificate cannot extend","NOT_AVAILABLE"],
  ["A13","operator trial budget <=24 and generations <=3","T-GSC6","design-only","registry count","proposal/validation only","unbounded search changes M/selection","REQUIRED"],
  ["A14","final evaluation read once after freeze","T-GSC6/7","design-only","access log","held-out evaluation","multiple looks need adjustment","REQUIRED"],
  ["A15","query/build bootstrap unit is correct","all empirical bridge claims","directly observable","bootstrap manifest","query vs build cluster","wrong unit overstates certainty","REQUIRED"],
]);

await save("claim_registry.csv",
  ["claim_id","claim","class","status","allowed_scope","evidence_needed","forbidden_extension"], [
  ["CL01","build history is a hidden condition variable","A","ALLOWED_WITH_CURRENT_EVIDENCE","Graph-ANNS budget decisions","inherited theory","none beyond scope"],
  ["CL02","source-only open-world transfer has risk/cost barriers","A","ALLOWED_WITH_RESTRICTED_SCOPE","declared environment class","outer assumptions for stronger version","unconditional impossibility for all settings"],
  ["CL03","Oracle headroom differs from observable gain","A","ALLOWED_WITH_CURRENT_EVIDENCE","oracle is upper bound","none","oracle gain equals deployment gain"],
  ["CL04","adaptive Generate then independent Certify is safe","C","RESTRICTED_THEOREM","frozen finite family/fixed target","split and alpha ledger","new adaptive inference theory"],
  ["CL05","ordinary CIBS has no two-dataset CI joint-feasible action","A","ALLOWED_WITH_FROZEN_CLOSURE_SCOPE","latest closure only","preserve frozen evidence level","general Graph-ANNS impossibility"],
  ["CL06","CFSR-Lite failure does not refute all stabilization","A","ALLOWED_WITH_RESTRICTED_SCOPE","tested operator family only","new operator evaluation","all stabilization impossible"],
  ["CL07","GSC creates a new Pareto point","B","PILOT_ONLY","registered datasets/tracks","independent NDC/Recall/p95","theory claim"],
  ["CL08","stabilization reduces cross-build response dispersion","B","PILOT_ONLY","measured D_Z/D_C","per-query responses and build clusters","D_C alone controls D_Z"],
  ["CL09","GSC reduces rejection/fallback","B","PILOT_ONLY","fixed-target service","acceptance/fallback logs","guaranteed reduction"],
  ["CL10","GSC has finite total-cost break-even","B","PILOT_ONLY","declared workload","all offline costs","proxy/oracle substitution"],
  ["CL11","response disagreement controls risk difference","C","RESTRICTED_THEOREM","fixed target and estimable disagreement","D_Z certificate","structure alone controls risk"],
  ["CL12","trace repair controls expansion-prefix","C","RESTRICTED_THEOREM","priority margin and fixed implementation","trace proof","raw-ef transfer"],
  ["CL13","first stable Graph-ANNS","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL14","first safe construction selection","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL15","first rebuild-portable ANNS","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL16","new generic Le Cam/KL lower bound","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL17","edge overlap guarantees budget stability","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL18","raw ef equals expansion","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL19","fixed-ef Recall is monotone","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL20","no target evidence needed","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL21","open-world safety solved","D","DO_NOT_CLAIM","none","none","any scope"],
  ["CL22","all metrics SOTA","D","DO_NOT_CLAIM","none","none","any scope"],
]);

console.log("created 8 inspected GSC CSV artifacts");
