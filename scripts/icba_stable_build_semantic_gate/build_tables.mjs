import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = process.env.ICBA_ROOT || path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const outDir = path.join(root, "results/icba_stable_build_semantic_gate");
const cell = v => /[",\n]/.test(String(v ?? "")) ? `"${String(v ?? "").replaceAll('"','""')}"` : String(v ?? "");
const csv = (h, rows) => [h,...rows].map(r=>r.map(cell).join(",")).join("\n")+"\n";
async function emit(name,h,rows){
  const body=csv(h,rows);
  const wb=await Workbook.fromCSV(body,{sheetName:name.slice(0,28)});
  const check=await wb.inspect({kind:"table",tableMaxRows:Math.min(5,rows.length+1),tableMaxCols:Math.min(12,h.length),maxChars:3000});
  if(!check.ndjson||!rows.length) throw new Error(`artifact validation failed: ${name}`);
  await fs.writeFile(path.join(outDir,name),body,"utf8");
  return [name,rows.length];
}

const litH=["paper_id","full_citation_short","year","venue","official_url","reading_level","actual_read_scope","modifies_construction","uses_query_trace","protects_critical_path","analyzes_frontier_or_rank","multiple_rebuilds","cross_build_stability","minimum_safe_budget","endpoint_censoring","formal_risk_or_certificate","target_labels","multi_build_validation","degree_constrained_repair","T_SC5_T_SC10_overlap","direct_prior_test","threat","remaining_gap"];
const lit=[
["L01","Ma et al., Sparse Neighborhood Graph-Based ANNS Revisited",2026,"arXiv v5","https://arxiv.org/abs/2509.15531","A","full HTML and appendices/proofs","yes","no","path structure","yes","no","no","no","no","search theorem; proof concern noted","no","no","graph optimization","STRONG_COMPONENT_OVERLAP","FAILS_2_4","CRITICAL","no rebuild safe-budget/certification"],
["L02","Yang et al., Revisiting the Index Construction of Proximity Graph-Based ANNS",2025,"PVLDB","https://www.vldb.org/pvldb/vol18/p4170-yang.pdf","A","full official paper; Thm 4.1, 4.2, 5.1 and proofs","yes","search/path statistics","implicit","path rank","no","no","no","no","path-quality bounds","no","no","yes","STRONG_COMPONENT_OVERLAP","FAILS_2_4","CRITICAL","no cross-build response object"],
["L03","Elliott and Clark, Impacts of Data, Ordering, and Intrinsic Dimensionality on Recall in HNSW",2024,"SISAP/arXiv","https://arxiv.org/abs/2405.17813","A","full paper","no","no","no","no","yes","empirical sensitivity","no","no","no","no","yes","no","PHENOMENON_OVERLAP","FAILS_1_3","CRITICAL","no stable method/theorem"],
["L04","Singh et al., FreshDiskANN",2021,"arXiv","https://arxiv.org/abs/2105.09613","A","full paper and appendices","yes","search-guided prune","no","no","updates/merges","dynamic recall not rebuild budget","no","no","no formal certificate","no","multi-update","FreshVamana prune","STRONG_COMPONENT_OVERLAP","FAILS_2_4","HIGH","no query-budget portability"],
["L05","Fu et al., NSG",2019,"PVLDB","https://doi.org/10.14778/3303753.3303754","A","full official paper","yes","search-produced candidates","monotonic paths","yes","no","no","no","no","no","no","no","degree prune/connectivity","STRONG_COMPONENT_OVERLAP","FAILS_2_4","HIGH","single-index recall/latency"],
["L06","Subramanya et al., DiskANN/Vamana",2019,"NeurIPS","https://papers.nips.cc/paper/9527-rand-nsg-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node","A","full proceedings paper","yes","beam search candidates","no","alpha-RNG rank","no","no","no","no","no","no","no","degree prune","STRONG_COMPONENT_OVERLAP","FAILS_2_4","HIGH","no rebuild response"],
["L07","Yenen, MonaVec",2026,"arXiv","https://arxiv.org/abs/2606.19458","A","full preprint","yes","no","no","no","deterministic replay","reproducibility only","no","no","no","no","yes","no","DETERMINISM_OVERLAP","FAILS_2_3","HIGH","determinism not safety stability"],
["L08","Wang et al., Steiner-Hardness",2024,"PVLDB","https://doi.org/10.14778/3704965.3704974","A","full paper and proofs","no","query effort","hardness subgraph","yes","no","no","effort proxy","no","theoretical hardness","no","no","no","STRONG_COST_OBJECT_OVERLAP","FAILS_1_2_4","CRITICAL","no construction/rebuild/certificate"],
["L09","Wang et al., ANNiE",2026,"PVLDB","https://doi.org/10.14778/3836663.3836728","A","full official 14-page paper","no","profiles fixed index","no","no","no","no","learned per-query cost","no","population quantile","yes","no","no","STRONG_BUDGET_OVERLAP","FAILS_1_2_4","CRITICAL","fixed-index learned estimator"],
["L10","MARGO: Select Edges Wisely",2025,"PVLDB","https://www.vldb.org/pvldb/vol18/p3820-wang.pdf","A","full official paper and theorem","page layout only","yes","monotonic path impact","yes","no","no","no","no","layout theorem not risk","workload traces","no","no","STRONG_COMPONENT_OVERLAP","FAILS_1_2_3_4","CRITICAL","physical layout not logical rebuild stability"]
];

const claims=[
["C01","Stable graph construction is new","DELETE","NSG/Vamana/FreshDiskANN/MARGO","broad claim false"],
["C02","Rebuild or insertion-order sensitivity is new","DELETE","Elliott and Clark","phenomenon known"],
["C03","T-SC5 directly guarantees hnswlib ef","DELETE","source audit plus CE01/CE02","implementation bridge not proved"],
["C04","One priority intruder costs one ef","DELETE","ef is not expansion counter","unit mismatch"],
["C05","Raw fixed-ef recall is upward closed","DELETE","CE07 tie-sensitive witness","only resumable envelope is closed"],
["C06","Edge overlap controls safe budget","DELETE","prior counterexamples/T-SC10","false generally"],
["C07","Cross-build query-effort stability is a distinct systems objective","RETAIN_NARROW","no four-condition direct prior","do not say first"],
["C08","ef, expansion, NDC, and time need separate contracts","RETAIN","hnswlib source audit","implementation-specific contribution"],
["C09","Trace-certificate repair plus empirical ef calibration","RETAIN_AS_TEMPLATE","Yang/MARGO/repair priors overlap","not validated algorithm"],
["C10","Endpoint/right-censor aware budget response","RETAIN_NARROW","no direct checked counterpart","Graph-ANNS scope only"]
];

const sem=[
["S01","requested ef","caller/index `ef_`","base argument max(ef_,k)","not an actual-work cap","OBSERVABLE"],
["S02","top-candidate capacity","top_candidates heap","admit while size<ef or better; trim >ef","capacity/retention rule","OBSERVABLE"],
["S03","candidate queue","candidate_set heap","separate from retained heap","not hard capped by ef","OBSERVABLE_WITH_TRACER"],
["S04","actual expansions","candidate pops expanded","loop-dependent","may exceed ef","OBSERVABLE_WITH_TRACER"],
["S05","NDC","distance-function calls","neighbor dependent","no deterministic Lipschitz map from ef","OBSERVABLE_WITH_COUNTER"],
["S06","wall time","timer around query","hardware/runtime dependent","not theorem-controlled","OBSERVABLE"],
["S07","visited","visited_array tag","marked before distance/admission","rejected nodes remain visited","OBSERVABLE_WITH_TRACER"],
["S08","stop rule bare-bone","candidate_dist > lowerBound","break","depends on retained heap","OBSERVABLE_WITH_TRACER"],
["S09","stop rule filter/deletion","candidate_dist > lowerBound && top_candidates.size()==ef","break","different branch","OBSERVABLE_WITH_TRACER"],
["S10","tie rule","CompareByFirst distance only","equal keys comparator-equivalent","no portable total order","NEEDS_EXPLICIT_SECONDARY_KEY"],
["S11","fixed-ef rerun","new search call","fresh visited/candidate state","not resumable prefix","VERIFIED"],
["S12","B_ef","minimum successful requested ef on declared grid","independent runs","endpoint-aware/right-censored","DEFINED"],
["S13","B_exp","minimum successful checkpoint in resumable deterministic search","prefix action","not native ef","DEFINED"],
["S14","bridge","B_exp to B_ef","none universal proved","empirical calibration only","NOT_PROVED"],
["S15","intruder","noncertificate competitor popped before required certificate node","trace event","count acts on expansion theorem only","OBSERVABLE_WITH_TRACER"]
];

const status=[
["T-SC5a","certificate disruption union bound","FORMAL_PROOF_COMPLETE","classical event decomposition","not a major novelty"],
["T-SC5b","deterministic expansion-prefix delay","FORMAL_PROOF_RESTRICTED","total tie order; frozen discovery/insertion; bounded prior intruders","does not mention native ef"],
["T-SC5c","native hnswlib ef delay","THEOREM_INVALID_FOR_EF_ACTION","required ef/prefix bridge absent","delete old interpretation"],
["T-SC10a","generic overlap cannot control budget","FORMAL_PROOF_RESTRICTED","finite counterexamples; declared budget action","valid negative boundary"],
["T-SC10b","robust certificate controls expansion surrogate","FORMAL_PROOF_RESTRICTED","same abstract assumptions as T-SC5b","restricted structural result"],
["T-SC10c","structure controls B_ef","EMPIRICAL_CALIBRATION_ONLY","independent calibration queries","not theorem implication"],
["Bridge-1","B_ef <= psi(B_exp)","IMPLEMENTATION_BRIDGE_NOT_PROVED","native independent search semantics","Interface C"],
["Closure-raw","fixed-ef raw recall upward closure","COUNTEREXAMPLE_FOUND","distance ties/non-total order","must not assume"],
["Closure-prefix","resumable best-so-far envelope","FORMAL_PROOF_COMPLETE","same run retains best-so-far","definition-level monotonicity"]
];
const patches=[
["P01","T-SC5 budget noun","ef","expansion-prefix/checkpoint count","removes unit conflation"],
["P02","T-SC5 tie assumption","fixed tie-breaking","declared total priority key including secondary ID","makes replay proposition well-defined"],
["P03","introduction edge","path edge","first successful candidate-queue insertion parent","unique under event log"],
["P04","intruder charge","+1 ef","+1 prior expansion in restricted model","no ef claim"],
["P05","endpoint","max ef","infinity/right-censored/uncertified","prevents false success"],
["P06","T-SC10 positive link","structural distance to budget","structural certificate to expansion surrogate; empirical to ef","scope correction"],
["P07","safe-set closure","raw fixed ef","resumable best-so-far prefix only","counterexample-safe"],
["P08","pilot role","theorem validation","empirical bridge test","prevents inference reversal"]
];

const obsFields=[
["query ID","yes","no","low","none","yes","yes","protocol"],["build ID","external","no","low","none","yes","yes","environment"],["source/target ID","yes","no","low","none","yes","yes","edge event"],["requested ef","yes","no","low","none","yes","yes","action"],["actual expansions","yes","project tracer","low","low","yes","yes","work"],["actual NDC","yes","counting metric","low","low","yes","yes","work"],["wall-clock","yes","no","low","timer noise","yes","no","cost"],["upper-layer path","yes","project tracer","medium","low","yes","yes","entry"],["base-layer expansion order","yes","project tracer","medium","low","yes","yes","prefix"],["candidate queue insertion order","yes","project tracer","high","low","yes","yes","introduction"],["introduction parent edge","reconstructible","project tracer","medium","low","yes","yes","certificate"],["priority key","yes","project tracer","medium","low","yes","conditional","frontier"],["top-candidate heap state","no","extend tracer","high","memory/timing","yes","yes","lowerBound"],["lowerBound changes","reconstructible","project tracer","medium","low","yes","yes","stop"],["visited state","reconstructible","project tracer","high","memory","yes","yes","discovery"],["first safe discovery","no","extend tracer plus design truth","high","truth/timing","yes","yes","safety"],["endpoint status","external","no","low","none","yes","yes","censoring"],["top-k result at checkpoint","no","extend tracer","high","memory","yes","yes","safety"],["candidate set at checkpoint","no","extend tracer","high","memory","yes","yes","frontier"],["backup path","no","offline derive from full trace","high","none offline","yes","conditional","backup"],["edge layer","yes","project tracer","low","low","yes","yes","layer"],["tie event","no","extend tracer","medium","low","yes","yes","total order"],["filtered/deleted node","no","extend tracer","medium","low","yes","yes","branch"],["search stop reason","no","extend tracer","low","low","yes","yes","termination"]
];

const ces=[
["CE01","ef is not expansion cap","ef=1; five expansions","PASS"],["CE02","fixed-ef traces need not be prefix-equivalent","equal-key branches","PASS"],["CE03","one intruder adds one abstract expansion","finite queue witness","PASS"],["CE04","one intruder need not raise global ef threshold","frontier-width witness","PASS"],["CE05","critical edge retention insufficient under tie change","equal keys reorder","PASS"],["CE06","introduction parent not graph intrinsic","two incoming edges","PASS"],["CE07","raw fixed-ef recall nonmonotone","tie-sensitive top-k","PASS"],["CE08","endpoint infeasible","B=infinity beyond grid","PASS"],["CE09","same expansions different NDC","degree variation","PASS"],["CE10","same mean NDC worse p95","finite vectors","PASS"],["CE11","fixed ef reruns versus resumable prefix","state reset","PASS"],["CE12","serialized replay consistency","canonical tiny state","PASS"],["CE13","visited before admission","rejected node remains visited","PASS"],["CE14","ef versus NDC","same ef varying degrees","PASS"],["CE15","requested ef versus capacity","capacity=max(ef,k)","PASS"],["CE16","best-so-far prefix closure","running envelope","PASS"]
];

const alg=[
["A01","critical edge","FROZEN","first successful insertion parent before first safe checkpoint","labeled design only"],["A02","path impact","FROZEN","weighted design/shadow frequency","pre-register weights"],["A03","frontier margin","FROZEN","gap to closest noncertificate competitor; tie zero","total key required"],["A04","intruder risk","FROZEN","shadow frequency or upper bound of prior pops","not ef delta"],["A05","backup edge","FROZEN","observed in r_min shadows and replay-admissible","trace dependent"],["A06","edge weight","FROZEN","lambda_c c + lambda_p p + lambda_b b + lambda_m clip(m) - lambda_i i","coefficients design-only"],["A07","shadow aggregation","FROZEN","mean plus preregistered lower confidence bound","no evaluation tuning"],["A08","degree overflow","FROZEN","mandatory first then diversity prune; invalid if mandatory>cap","rollback"],["A09","connectivity","FROZEN","entry directed reachability plus weak connectivity","rollback on failure"],["A10","layer scope","FROZEN","layer 0 only","upper layers unchanged"],["A11","entry point","FROZEN","unchanged","manifested"],["A12","operation order","FROZEN","post-build repair then reverse-prune audit then serialization","verify protected survival"],["A13","complexity","BOUNDED_SPEC","linear trace aggregation plus local sort/prune","graph reachability extra"],["A14","memory","BOUNDED_SPEC","per-edge aggregates under byte cap","full trace exported then discarded"],["A15","serialization","FROZEN","native index plus sidecar manifest and SHA256","versioned schema"],["A16","invalid certificate fallback","FROZEN","unmodified build or declared consensus route","no inferred safety"],["A17","labeled vs unlabeled","FROZEN","unlabeled is trace-stability heuristic only","no safety-critical wording"]
];

await fs.mkdir(outDir,{recursive:true});
const out=[];
out.push(await emit("directed_literature_matrix.csv",litH,lit));
out.push(await emit("prior_art_claim_crosswalk.csv",["claim_id","claim","decision","basis","qualification"],claims));
out.push(await emit("search_semantic_crosswalk.csv",["semantic_id","object","implementation_location","exact_semantics","theory_consequence","status"],sem));
out.push(await emit("theorem_status.csv",["result_id","statement","status","assumptions_or_basis","disposition"],status));
out.push(await emit("theorem_patch_ledger.csv",["patch_id","location","old_text_or_semantics","replacement","reason"],patches));
out.push(await emit("observability_matrix.csv",["field","currently_observable","modification","cost","semantic_interference","serializable","exact_replay","theory_assumption"],obsFields));
out.push(await emit("semantic_counterexamples.csv",["case_id","property","witness","status"],ces));
out.push(await emit("algorithm_readiness_gate.csv",["item_id","component","status","frozen_definition","constraint"],alg));
console.log(JSON.stringify(out));
