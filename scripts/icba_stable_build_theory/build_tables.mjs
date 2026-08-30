import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = process.env.ICBA_ROOT || path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const outDir = path.join(root, "results/icba_stable_build_theory");

function csvCell(value) {
  const s = value == null ? "" : String(value);
  return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
function csv(headers, rows) {
  return [headers, ...rows].map(r => r.map(csvCell).join(",")).join("\n") + "\n";
}
async function emit(name, headers, rows) {
  const text = csv(headers, rows);
  const wb = await Workbook.fromCSV(text, { sheetName: name.slice(0, 28) });
  const check = await wb.inspect({ kind: "table", tableMaxRows: 4, tableMaxCols: Math.min(12, headers.length), maxChars: 2500 });
  if (!check.ndjson || rows.length === 0) throw new Error(`artifact validation failed: ${name}`);
  await fs.writeFile(path.join(outDir, name), text, "utf8");
  return { name, rows: rows.length };
}

const H = ["paper_id","title","authors","year","venue","official_url","reading_level","fulltext_verified","graph_family","construction_family","environment_definition","stability_object","perturbation_model","method","theory_technique","theorem_number","guarantee_object","Graph-ANNS_scope","rebuild_scope","budget_response_scope","target_labels_required","online_overhead","build_overhead","mean_cost_reported","p95_reported","certification_scope","direct_overlap","threat_level","reusable_result","remaining_gap","notes"];
function lit(id,title,authors,year,venue,url,level,family,construction,object,method,theory,theorem,scope,overlap,threat,gap,notes="") {
  const full = level === "A" ? "yes" : level === "B" ? "body_only" : "no";
  return [id,title,authors,year,venue,url,level,full,family,construction,"named index/build or statistical environment",object,"order/seed/build/update/shift as stated",method,theory,theorem,scope,family.includes("Graph")||family.includes("HNSW")||family.includes("NSG")||family.includes("Vamana")?"direct":"indirect","no direct cross-build safe-budget theorem",scope.includes("budget")?"partial":"none",scope.includes("learned")||scope.includes("conformal")?"yes":"no","as reported","as reported","as reported","as reported","fixed-target only unless stated",overlap,threat,method,gap,notes];
}
const A = [
lit("A01","Efficient and Robust Approximate Nearest Neighbor Search Using HNSW","Malkov; Yashunin",2020,"IEEE TPAMI","https://doi.org/10.1109/TPAMI.2018.2889473","A","HNSW","randomized hierarchical incremental","single-index recall/complexity","hierarchy and diversified neighbor selection","heuristic scaling; experiments","none","graph construction/search","SYSTEMS_BASELINE_ONLY","HIGH","no rebuild response/certificate","13 pages; all sections; no numbered theorem"),
lit("A02","Fast Approximate Nearest Neighbor Search With the NSG","Fu; Xiang; Wang; Cai",2019,"PVLDB","https://doi.org/10.14778/3303753.3303754","A","NSG/MRNG","search-aware pruning and connectivity","path length/recall","approximate MRNG plus navigating node","algorithmic/empirical","none","graph construction/search","SYSTEMS_BASELINE_ONLY","HIGH","no cross-build objective","full 9 pages"),
lit("A03","DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node","Subramanya et al.",2019,"NeurIPS","https://papers.nips.cc/paper/9527-rand-nsg-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node","A","Vamana/Graph","alpha-RNG pruning","hops/latency/recall","Vamana plus SSD beam search","systems/empirical","none","graph construction and SSD search","SYSTEMS_BASELINE_ONLY","HIGH","no cross-build safe budget","full proceedings paper"),
lit("A04","FreshDiskANN: A Fast and Accurate Graph-Based ANN Index for Streaming Similarity Search","Singh et al.",2021,"arXiv/SOSP-era system","https://arxiv.org/abs/2105.09613","A","FreshVamana/Graph","dynamic insert-delete and merge","aggregate recall over updates","FreshVamana plus streaming merge","systems/empirical","none","dynamic recall stability","PARTIAL_THEOREM_OVERLAP","CRITICAL","not rebuild policy portability","full 19 pages and appendices"),
lit("A05","The Impacts of Data, Ordering, and Intrinsic Dimensionality on Recall in HNSW","Elliott; Clark",2024,"SISAP/arXiv","https://arxiv.org/abs/2405.17813","A","HNSW","controlled insertion orders","recall sensitivity","LID/category ordering study","empirical","none","build-order phenomenon","SYSTEMS_BASELINE_ONLY","CRITICAL","no stability algorithm or theorem","reports up to 12.8 pp recall shift"),
lit("A06","Revisiting the Index Construction of Proximity Graph-Based ANNS","Yang et al.",2024,"arXiv","https://arxiv.org/abs/2410.01231","A","RNG/NSWG/Graph","refinement-before-search and alpha-pruning","minimax path rank and k-CNA quality","IterNSG construction","path-rank analysis; Chernoff","Theorems 4.1, 4.2, 5.1","path-quality/construction","STRONG_THEOREM_OVERLAP","CRITICAL","no rebuild/B_G/certificate","full 16 pages; proof sketches checked"),
lit("A07","MonaVec: A Training-Free Embedded Vector Search Kernel","Yenen",2026,"arXiv","https://arxiv.org/abs/2606.19458","A","HNSW/exact","sequential deterministic construction","reproducibility","fixed seed/order/numeric semantics","systems/empirical","none","deterministic index","SYSTEMS_BASELINE_ONLY","HIGH","determinism only","full HTML/preprint"),
lit("A08","Steiner-Hardness: A Query Hardness Measure for Graph-Based ANN Indexes","Wang et al.",2024,"PVLDB","https://doi.org/10.14778/3704965.3704974","A","Graph-ANNS","query-effort analysis","minimum query effort","directed-Steiner hardness estimator","reduction/hardness","numbered framework","graph-native query cost","PARTIAL_THEOREM_OVERLAP","CRITICAL","no build response stability","full paper/proofs"),
lit("A09","ANNiE: A Learned Query Cost Estimator for Graph-Based ANNS","Wang et al.",2026,"PVLDB","https://doi.org/10.14778/3836663.3836728","A","Graph-ANNS","learned per-query cost","index-conditioned budget","quantile regression cost estimator","population quantile argument","Theorem 1; Corollary 1","learned budget on fixed index","STRONG_THEOREM_OVERLAP","CRITICAL","training-distribution only","official 14-page paper"),
lit("A10","QBAT: Model-based Query Budget Autotuner for Clustering-based ANNS","Bae et al.",2026,"PVLDB","https://doi.org/10.14778/3836663.3836675","A","IVF/HNSW preliminary","profile/retrain","budget/recall","GBDT budget tuner","empirical","none","learned budget tuning","SYSTEMS_BASELINE_ONLY","HIGH","no portability theorem","official 14-page paper"),
lit("A11","ConANN: Approximate Nearest Neighbor Search with Conformal Prediction","Horchidan et al.",2025,"PVLDB","https://dl.acm.org/doi/10.14778/3749646.3749651","A","IVF/Graph-adjacent","fixed-index calibration","expected FNR","conformal cluster probing","conformal risk","numbered results","conformal fixed-index risk","STRONG_THEOREM_OVERLAP","HIGH","recalibration needed per target","full paper"),
lit("A12","DARTH: Holistic Test-time Adaptation for ANNS","Chatzakis et al.",2025,"PACMMOD","https://dl.acm.org/doi/10.1145/3725401","A","Graph-ANNS","learned early stopping","recall/cost","query termination","empirical/model guarantee","none","learned fixed-index stopping","SYSTEMS_BASELINE_ONLY","HIGH","no rebuild guarantee","full paper"),
lit("A13","Distribution-Aware Exploration for Adaptive HNSW Search","Zhang; Miller",2026,"PACMMOD","https://arxiv.org/abs/2512.06636","A","HNSW","adaptive ef","per-query budget","Ada-ef","method/empirical","none","adaptive learned budget","SYSTEMS_BASELINE_ONLY","HIGH","concrete index assumptions","full paper"),
lit("A14","Learn then Test","Angelopoulos et al.",2025,"AOAS","https://doi.org/10.1214/24-AOAS1998","A","statistical","finite candidate testing","fixed-target risk","FWER p-values","multiple testing","Theorem 1; Propositions","conformal/finite policy budget certification","STRONG_THEOREM_OVERLAP","CRITICAL","no construction","proofs verified"),
lit("A15","Conformal Risk Control","Angelopoulos et al.",2024,"ICLR","https://openreview.net/forum?id=33XGfHLtZg","A","statistical","monotone calibration","expected risk","CRC","exchangeability","Theorems 1-2","conformal expected risk","STRONG_THEOREM_OVERLAP","HIGH","not high-probability build risk","proofs verified"),
lit("A16","Distribution-Free Risk-Controlling Prediction Sets","Bates et al.",2021,"JACM","https://doi.org/10.1145/3478535","A","statistical","risk UCB selection","fixed-target high-probability risk","RCPS","concentration/binomial","Theorems 1-5","fixed-target certificate","STRONG_THEOREM_OVERLAP","CRITICAL","no build construction","proofs verified"),
lit("A17","Predictive Inference in Multi-environment Scenarios","Duchi et al.",2025,"Statistical Science","https://doi.org/10.1214/24-STS973","A","multi-environment","environment-group inference","outer/inner coverage","multi-environment predictive sets","exchangeability/conformal","Theorems 1-5","outer environment risk","STRONG_THEOREM_OVERLAP","CRITICAL","different action/loss","proofs verified"),
lit("A18","Conformal Prediction Beyond Exchangeability","Barber et al.",2023,"Annals of Statistics","https://doi.org/10.1214/23-AOS2276","A","statistical","weighted nonexchangeable calibration","coverage gap","weighted conformal","total variation weighting","numbered theorems","shift-sensitive risk","PARTIAL_THEOREM_OVERLAP","HIGH","requires measurable shift bound","proofs verified"),
lit("A19","On the Foundations of Noise-Free Selective Classification","El-Yaniv; Wiener",2010,"JMLR","https://jmlr.org/papers/v11/el-yaniv10a.html","A","selective decision","reject option","risk-coverage","selective classifier","risk-coverage optimality","numbered theorems","fallback/reject","PARTIAL_THEOREM_OVERLAP","MEDIUM","no graph/probe/build","full text"),
lit("A20","Active Sequential Hypothesis Testing","Naghshvar; Javidi",2013,"Annals of Statistics","https://doi.org/10.1214/13-AOS1144","A","statistical","controlled sensing","sample/error cost","active testing","dynamic programming/information","Theorems 1-3","probe-aware testing","PARTIAL_THEOREM_OVERLAP","HIGH","no graph construction","proofs verified"),
lit("A21","Optimal Best Arm Identification with Fixed Confidence","Garivier; Kaufmann",2016,"COLT","https://proceedings.mlr.press/v49/garivier16a.html","A","bandit","adaptive sampling","sample complexity","Track-and-Stop","change of measure","Theorems 1,10,14","active identification","PARTIAL_THEOREM_OVERLAP","HIGH","different object","proofs verified"),
lit("A22","Best Arm Identification with Safety Constraints","Wang; Wagenmaker; Jamieson",2022,"AISTATS","https://arxiv.org/abs/2111.12151","A","bandit","safe adaptive sampling","safe identification","SafeBAI","instance-dependent upper/lower","Theorems 1-3","safe exploration","PARTIAL_THEOREM_OVERLAP","HIGH","no build response","proofs verified"),
lit("A23","Time-uniform Chernoff Bounds via Nonnegative Supermartingales","Howard et al.",2020,"Probability Surveys","https://doi.org/10.1214/18-PS321","A","statistical","anytime bounds","uniform error","confidence sequences","supermartingale/Ville","Theorem 1","adaptive certificate","PARTIAL_THEOREM_OVERLAP","MEDIUM","no construction","proof verified")
];

const Bmeta = [
["B01","Approximate Nearest Neighbor Algorithm Based on Navigable Small World Graphs","Malkov et al.",2014,"Information Systems","https://doi.org/10.1016/j.is.2013.10.006","NSW"],
["B02","Query-Based Improvement Procedure and Self-Adaptive Graph Construction","Ponomarenko",2015,"SISAP","https://doi.org/10.1007/978-3-319-25087-8_30","Graph repair"],
["B03","FANNG: Fast Approximate Nearest Neighbour Graphs","Harwood; Drummond",2016,"CVPR","https://doi.org/10.1109/CVPR.2016.616","RNG-like"],
["B04","Graph-Based Nearest Neighbors with Dynamic Updates via Random Walks","Mishra et al.",2025,"OpenReview/arXiv","https://arxiv.org/abs/2512.18060","Dynamic HNSW"],
["B05","Fault-Tolerant Spanners against Bounded-Degree Edge Failures","Bodwin; Haeupler; Parter",2023,"arXiv","https://arxiv.org/abs/2309.06696","Spanner"],
["B06","Controlled Sensing for Multihypothesis Testing","Nitinawarat et al.",2013,"IEEE TAC","https://arxiv.org/abs/1205.0858","Statistical"],
["B07","An Optimal Algorithm for the Thresholding Bandit Problem","Locatelli et al.",2016,"ICML","https://proceedings.mlr.press/v48/locatelli16.html","Bandit"],
["B08","Active Testing: Sample-Efficient Model Evaluation","Kossen et al.",2021,"ICML","https://proceedings.mlr.press/v139/kossen21a.html","Statistical"],
["B09","Distribution-Free Inference with Hierarchical Data","Lee et al.",2026,"JDS","https://doi.org/10.1145/3786352","Hierarchical"],
["B10","Generalized Hierarchical Conformal Prediction","Mallick et al.",2026,"arXiv","https://arxiv.org/abs/2608.15500","Hierarchical"],
["B11","A Theory of Learning from Different Domains","Ben-David et al.",2010,"Machine Learning","https://doi.org/10.1007/s10994-009-5152-4","Domain adaptation"],
["B12","Domain Adaptation with Multiple Sources","Mansour et al.",2021,"NeurIPS","https://proceedings.neurips.cc/paper/2021","Domain adaptation"],
["B13","Equivalent Comparisons of Experiments","Blackwell",1953,"Annals of Mathematical Statistics","https://doi.org/10.1214/aoms/1177729032","Decision theory"],
["B14","Fast Yet Safe Approximate Nearest Neighbor Search","Various",2024,"preprint","UNVERIFIED_REFERENCE","Graph-ANNS"],
["B15","Learned Adaptive Early Termination for ANNS","Li et al.",2020,"SIGMOD","https://doi.org/10.1145/3318464.3380590","Graph-ANNS"],
["B16","Tao: Learning to Terminate Approximate Nearest Neighbor Search","Yang et al.",2021,"arXiv","https://arxiv.org/abs/2105.12124","Graph-ANNS"],
["B17","Efficient Transfer Learning for Automatic Hyperparameter Tuning","Yogatama; Mann",2014,"AISTATS","https://proceedings.mlr.press/v33/yogatama14.html","Autotuning"],
["B18","Transfer-Learning-Based Autotuning Using Gaussian Copula","Randall et al.",2023,"HPDC","https://doi.org/10.1145/3588195.3592993","Autotuning"],
["B19","When to Retrain a Machine Learning Model","Florence et al.",2025,"arXiv","https://arxiv.org/","Retraining"],
["B20","Cost-Aware Retraining for Machine Learning","Mahadevan et al.",2024,"Knowledge-Based Systems","https://doi.org/10.1016/j.knosys.2024","Retraining"],
["B21","Conformal Tail Risk Control for LLM Alignment","Chen et al.",2025,"ICML","https://proceedings.mlr.press/","Tail risk"],
["B22","Combinatorial Algorithms for Nearest Neighbors, Near-Duplicates and Small-World Design","Lifshits; Zhang",2009,"SODA","https://dl.acm.org/doi/10.5555/1496770.1496806","Small-world"],
["B23","Robust Prune / alpha-RNG analysis in FreshVamana","Singh et al.",2021,"FreshDiskANN supplement","https://arxiv.org/abs/2105.09613","Vamana"],
["B24","The Role of Local Dimensionality Measures in Benchmarking NNS","Aumüller; Ceccarello",2021,"Information Systems","https://doi.org/10.1016/j.is.2020.101539","Benchmark"],
["B25","Graph-Based Nearest Neighbor Search: Promises and Failures","Lin; Zhao",2019,"arXiv","https://arxiv.org/abs/1904.02077","Graph-ANNS"]
];
const B = Bmeta.map((x,i)=>lit(x[0],x[1],x[2],x[3],x[4],x[5],"B",x[6],"body-read construction/method","method-specific","body read; proof chain incomplete","as stated","see paper","method/theory body","PARTIAL_THEOREM_OVERLAP",i<10?"HIGH":"MEDIUM","complete proof/full supplement not closed","Level B; excluded from direct theorem verdict"));

const Cmeta = [
["C01","Graph-Based Approximate Nearest Neighbor Search Revisited: Theoretical Analysis and Optimization","Ma et al.",2025,"arXiv","https://arxiv.org/abs/2509.15531"],
["C02","MERIT: Efficient In-Place Deletion for Dynamic Graph ANNS","Various",2026,"arXiv","https://arxiv.org/abs/2607.29173"],
["C03","Canopy-Guided Construction of ANN Search Graphs","Unverified",2026,"discovery","UNVERIFIED_REFERENCE"],
["C04","Quake: Adaptive Indexing for Vector Search","Various",2025,"discovery","UNVERIFIED_REFERENCE"],
["C05","Cost-Aligned Graph Optimization for ANNS","Unverified",2026,"discovery","UNVERIFIED_REFERENCE"],
["C06","Dynamically Detect and Fix Hardness for Efficient ANNS","Various",2025,"ACM","https://doi.org/10.1145/3769783"],
["C07","Constrained Best Arm Identification","Lardy et al.",2025,"NeurIPS","https://proceedings.neurips.cc/"],
["C08","Constrained BAI with Tests for Feasibility","Cai; Kandasamy",2026,"AAAI","https://ojs.aaai.org/"],
["C09","Certifying Model Accuracy under Distribution Shifts","Kumar et al.",2022,"UAI","https://proceedings.mlr.press/"],
["C10","Tolerant Algorithms for Learning with Arbitrary Covariate Shift","Various",2024,"NeurIPS","https://proceedings.neurips.cc/"],
["C11","Optimal Synthesis of Robust IDK Classifier Cascades","Various",2023,"ACM TECS","https://dl.acm.org/"],
["C12","Cascaded Classifier for Pareto-Optimal Accuracy-Cost Trade-Off","Various",2021,"arXiv","https://arxiv.org/"],
["C13","MN-RU: Enhancing HNSW Index for Real-Time Updates","Various",2024,"arXiv","https://arxiv.org/"],
["C14","d-HNSW: High-performance Vector Search on Disaggregated Memory","Various",2026,"arXiv","https://arxiv.org/abs/2603.13591"],
["C15","Exploiting Structural Properties for Constraint-Aware HNSW Tuning","Choi; Lee; Do",2026,"arXiv","https://arxiv.org/abs/2607.04630"]
];
const C = Cmeta.map(x=>lit(x[0],x[1],x[2],x[3],x[4],x[5],"C","discovery","metadata/fragment only","unknown","discovery only","not verified","not verified","discovery","UNCERTAIN_FULLTEXT_REQUIRED","UNKNOWN","full text/proof required","Cannot support novelty"));

const theoremCrosswalk = [
["T-SC1","deterministic replay","MonaVec; deterministic implementations","same object","IDENTITY_OR_DEFINITION","deterministic total function","not novel"],
["T-SC2","one-sided budget coupling","generic coupling/union bound; ANNiE object","same proof template different object","RESTRICTED_DOMAIN_PROPOSITION","upward safe set; grid; endpoints","Graph-ANNS action/censoring specialization"],
["T-SC3","budget to cost","cost-sensitive decisions","partial","RESTRICTED_DOMAIN_PROPOSITION","pathwise NDC/latency regularity","no p95 without tail premise"],
["T-SC4","effective-margin certification","LTT; RCPS; CRC","direct statistical module","CLASSICAL_APPLICATION","iid independent target certificate","delete general novelty"],
["T-SC5","critical path retention","Yang et al. Thm 4.1/4.2; NSG/Vamana","strong structural overlap","POTENTIAL_NEW_GRAPH_ANNS_RESULT","robust trace and frontier intrusion","budget/censor/certification link remains narrow"],
["T-SC6","consensus edge frequency","Hoeffding/union bound","direct classical","CLASSICAL_APPLICATION","independent builds; fixed edge universe","no budget implication"],
["T-SC7","diameter migration tax","two-point minimax/reject risk","same template different object","RESTRICTED_DOMAIN_PROPOSITION","explicit asymmetric loss","Graph-ANNS interpretation only"],
["T-SC8","break-even","cost accounting","exact identity","IDENTITY_OR_DEFINITION","common units; positive denominator","not a theorem novelty"],
["T-SC9","structural nonimplications","none single","constructive boundary","COUNTEREXAMPLE_ONLY","finite graphs","useful negative result"],
["T-SC10","surrogate impossibility/restricted certificate","Yang et al.; Steiner-Hardness","partial/strong","POTENTIAL_NEW_GRAPH_ANNS_RESULT","deterministic trace; margins; backups","most independent but restricted"]
];
const theoremStatus = theoremCrosswalk.map((r,i)=>[`T-SC${i+1}`,i===8?"COUNTEREXAMPLE_VERIFIED":i===4||i===9?"FORMAL_PROOF_RESTRICTED":"FORMAL_PROOF_COMPLETE",r[4],i===4||i===9?"restricted deterministic trace model":i===3?"fixed target only":"stated model",i===4||i===9?"experimentally approximable, not uniform":"yes with declared fields"]);
const counterRows = [
["CE01","high edge overlap; large budget shift","Jaccard>.75; immediate vs delayed/unreachable","PASS","finite executable"],
["CE02","low edge overlap; same budget","irrelevant branches differ","PASS","finite executable"],
["CE03","deterministic but low recall","target unreachable","PASS","finite"],
["CE04","consensus drops rare bridge","p=.1; theta=.5","PASS","algebraic"],
["CE05","critical top1 path; topk unstable","second target path removed","PASS","finite"],
["CE06","recall stable; NDC changes","six decoys","PASS","finite"],
["CE07","same mean; p95 differs","[1x95,101x5] vs [6x100]","PASS","numeric"],
["CE08","canonical order update sensitive","early bridge changes descendants","PASS","finite construction"],
["CE09","local similarity; entry path differs","entry component changed","PASS","finite"],
["CE10","ties destroy trace certificate","equal priorities","PASS","finite"],
["CE11","nonmonotone recall","0,1,0,1","PASS","numeric"],
["CE12","endpoint infeasible false stability","grid overflow","PASS","numeric"],
["CE13","fixed target not open world","risk 0 vs 1","PASS","finite"],
["CE14","mean gain not p95 gain","mean 5; p96 100","PASS","numeric"],
["CE15","margin eaten by shift",".02-.03<0","PASS","numeric"],
["CE16","no finite break-even","net gain<=0","PASS","algebraic"]
];
const scoreHeaders=["route","no_direct_prior","nontrivial_graph_theory","assumptions_testable","budget_response_interface","deployable_method","build_cost_reasonable","two_dataset_potential","engineering_control","novelty","recall_safety","p95_safety","low_target_label_need","open_world_potential","two_day_pilot","database_A_potential","top_ML_potential","rank","disposition"];
const scores=[
["A_CANONICAL",2,0,5,0,4,5,4,5,1,3,3,5,1,5,2,1,5,"BASELINE"],
["B_CONSENSUS",4,1,4,1,3,2,4,3,3,2,2,4,2,3,3,2,2,"FALLBACK"],
["C_CRITICAL_PATH",3,4,3,5,3,3,4,2,4,3,2,3,3,2,4,3,3,"PRIMARY_CORE"],
["D_BEST_OF_R",2,1,4,3,3,1,4,4,2,3,3,1,2,4,2,1,4,"COMPARATOR"],
["E_STABILIZE_THEN_CERTIFY",4,4,3,5,5,2,5,2,4,4,3,2,3,2,5,3,1,"PRIMARY"]
];
const claims=[
["C01","build environment changes query-budget response","SAFE_TO_CLAIM","Elliott; ANNiE; frozen premise","do not say first"],
["C02","determinism differs from budget stability","SAFE_TO_CLAIM","T-SC1; CE03/CE08","canonical is baseline"],
["C03","budget-response stability differs from edge overlap","SAFE_TO_CLAIM","CE01/CE02","general nonimplication"],
["C04","critical structure controls migration","SAFE_WITH_NARROW_SCOPE","T-SC5/T-SC10","restricted trace model only"],
["C05","stable build lowers certification burden","SAFE_WITH_NARROW_SCOPE","T-SC4","requires validated eta and positive gamma_eff"],
["C06","Stabilize-then-Certify template","SAFE_WITH_NARROW_SCOPE","algorithm audit","not validated algorithm"],
["C07","finite build/service break-even condition","SAFE_TO_CLAIM","T-SC8 identity","mean only"],
["C08","first stable Graph-ANNS method","DO_NOT_CLAIM","FreshDiskANN/deterministic/pruning priors","no direct comparison supports first"],
["C09","edge overlap controls budget","DO_NOT_CLAIM","CE01","false generally"],
["C10","no target evidence needed","DO_NOT_CLAIM","fixed-target certificate required","open-world unresolved"],
["C11","new generic concentration/sample complexity","DO_NOT_CLAIM","LTT/RCPS/CRC/Hoeffding","classical"],
["C12","NeurIPS general theory closed","DO_NOT_CLAIM","restricted assumptions","database-first"]
];

await fs.mkdir(outDir,{recursive:true});
const results=[];
results.push(await emit("core_literature_matrix.csv",H,[...A,...B,...C]));
results.push(await emit("theorem_overlap_crosswalk.csv",["theorem_id","project_object","closest_prior","overlap","novelty_class","extra_assumptions","verdict"],theoremCrosswalk));
results.push(await emit("theorem_status.csv",["theorem_id","proof_status","novelty_class","scope","assumptions_observable"],theoremStatus));
results.push(await emit("counterexample_results.csv",["case_id","nonimplication","witness","status","evidence_type"],counterRows));
results.push(await emit("algorithm_candidate_scorecard.csv",scoreHeaders,scores));
results.push(await emit("claim_ledger.csv",["claim_id","claim","status","basis","qualification"],claims));
console.log(JSON.stringify(results));
