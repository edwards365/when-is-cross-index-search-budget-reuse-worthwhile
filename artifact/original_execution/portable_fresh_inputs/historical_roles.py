"""Unchanged historical role selection and exact-content scan functions."""
import hashlib
import json
import numpy as np

ROLE_NAMES = ('source_design', 'target_selection', 'target_certification', 'target_evaluation')

def fresh_ids(name, seed, available, counts):
    key = hashlib.sha256(f"{name}:{seed}".encode("ascii")).digest()
    generator = np.random.Generator(np.random.PCG64(int.from_bytes(key[:8], "little")))
    chosen = generator.choice(available, size=sum(counts.values()), replace=False)
    answer = {}
    cursor = 0
    for role in ROLE_NAMES:
        count = counts[role]
        answer[role] = np.sort(chosen[cursor:cursor + count]).astype(np.int64)
        cursor += count
    return answer

def scan_content(train, all_query_ids, all_roles):
    query_vectors = np.asarray(train[all_query_ids.tolist()], dtype=np.float32)
    known = {}
    query_duplicates = []
    for raw_id, vector in zip(all_query_ids.tolist(), query_vectors):
        digest = hashlib.sha256(vector.tobytes(order="C")).digest()
        if digest in known and np.array_equal(known[digest][1], vector):
            query_duplicates.append([known[digest][0], raw_id])
        else:
            known[digest] = (raw_id, vector.copy())
    query_set = set(all_query_ids.tolist())
    counterparts = []
    for begin in range(0, len(train), 2048):
        block = np.asarray(train[begin:begin + 2048], dtype=np.float32)
        for offset, vector in enumerate(block):
            raw_id = begin + offset
            if raw_id in query_set:
                continue
            digest = hashlib.sha256(vector.tobytes(order="C")).digest()
            prior = known.get(digest)
            if prior is not None and np.array_equal(prior[1], vector):
                counterparts.append([prior[0], raw_id, all_roles[prior[0]]])
        if begin == 0 or (begin // 2048 + 1) % 100 == 0:
            print(json.dumps({"content_scan_rows": min(begin + 2048, len(train)),
                              "total": len(train)}), flush=True)
    return query_duplicates, counterparts
