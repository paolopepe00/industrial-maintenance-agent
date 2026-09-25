import json
import time
import requests
from pathlib import Path

EVAL_FILE = Path("data/evaluation/eval_dataset.json")
AGENT_URL = "http://localhost:8000/chat"


def load_dataset():
    with open(EVAL_FILE) as f:
        return json.load(f)


def run_single(item, thread_prefix):
    thread_id = f"{thread_prefix}-{item['id']}"
    start = time.time()
    resp = requests.post(AGENT_URL, json={"message": item["question"], "thread_id": thread_id})
    latency = time.time() - start

    data = resp.json()
    answer = data.get("answer", "").lower()
    tool_calls_raw = data.get("tool_calls", [])
    called_tools = {tc.split("(")[0] for tc in tool_calls_raw}

    expected_tools = set(item["expected_tools"])
    tool_selection_ok = expected_tools.issubset(called_tools) if expected_tools else True
    no_unexpected_write = "create_work_order" not in called_tools  # safety check implicito

    keywords_found = [kw for kw in item["expected_keywords"] if kw.lower() in answer]
    keyword_ok = len(keywords_found) == len(item["expected_keywords"])

    forbidden_found = [kw for kw in item.get("forbidden_keywords", []) if kw.lower() in answer]
    no_forbidden = len(forbidden_found) == 0

    passed = tool_selection_ok and keyword_ok and no_forbidden

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "passed": passed,
        "tool_selection_ok": tool_selection_ok,
        "expected_tools": list(expected_tools),
        "called_tools": list(called_tools),
        "keyword_ok": keyword_ok,
        "missing_keywords": [kw for kw in item["expected_keywords"] if kw not in keywords_found],
        "no_forbidden": no_forbidden,
        "forbidden_found": forbidden_found,
        "latency_s": round(latency, 2),
        "answer": data.get("answer", ""),
    }


def main():
    dataset = load_dataset()
    results = [run_single(item, thread_prefix="eval-run") for item in dataset]

    total = len(results)
    passed = sum(r["passed"] for r in results)
    tool_ok = sum(r["tool_selection_ok"] for r in results)
    keyword_ok = sum(r["keyword_ok"] for r in results)
    avg_latency = sum(r["latency_s"] for r in results) / total

    print(f"\n{'='*60}")
    print(f"RISULTATI: {passed}/{total} passati ({passed/total*100:.0f}%)")
    print(f"Tool selection corretto: {tool_ok}/{total}")
    print(f"Keyword match corretto: {keyword_ok}/{total}")
    print(f"Latenza media: {avg_latency:.2f}s")
    print(f"{'='*60}\n")

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['id']} ({r['category']}) — {r['latency_s']}s")
        if not r["passed"]:
            if not r["tool_selection_ok"]:
                print(f"   tool atteso: {r['expected_tools']}, chiamato: {r['called_tools']}")
            if not r["keyword_ok"]:
                print(f"   keyword mancanti: {r['missing_keywords']}")
            if not r["no_forbidden"]:
                print(f"   keyword vietate trovate: {r['forbidden_found']}")

    out_path = Path("data/evaluation/results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDettagli completi salvati in {out_path}")


if __name__ == "__main__":
    main()