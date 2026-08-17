"""CLI helpers for indexing PDFs and running retrieval eval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from rag.pipeline.ingest import ingest_pdf_file
from rag.pipeline.query import answer_question
from rag.schemas import QueryRequest
from rag.store.supabase_store import RagStoreError


def cmd_ingest(args: argparse.Namespace) -> int:
    try:
        result = ingest_pdf_file(
            str(args.pdf),
            subject=args.subject,
            grade=args.grade,
            title=args.title,
            force=args.force,
        )
    except RagStoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result.model_dump(), indent=2))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    with open(args.file, encoding="utf-8") as handle:
        cases = json.load(handle)

    passed = 0
    results = []
    for case in cases:
        response = answer_question(
            QueryRequest(
                query=case["query"],
                grade=case["grade"],
                subject=case["subject"],
                chapter=case.get("chapter"),
            )
        )
        keywords = [keyword.lower() for keyword in case.get("expect_keywords", [])]
        answer_lower = response.answer.lower()
        ok = all(keyword in answer_lower for keyword in keywords) if keywords else bool(response.answer.strip())
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        results.append(
            {
                "query": case["query"],
                "status": status,
                "answer": response.answer,
                "rewritten_query": response.rewritten_query,
            }
        )

    print(json.dumps({"results": results, "passed": passed, "total": len(cases)}, indent=2))
    print(f"{passed}/{len(cases)} checks passed")
    return 0 if passed == len(cases) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartBatch RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Index a textbook PDF")
    ingest_parser.add_argument("pdf", type=Path, help="Path to PDF file")
    ingest_parser.add_argument("--subject", required=True)
    ingest_parser.add_argument("--grade", type=int, required=True)
    ingest_parser.add_argument("--title", default="Untitled")
    ingest_parser.add_argument("--force", action="store_true")
    ingest_parser.set_defaults(func=cmd_ingest)

    eval_parser = subparsers.add_parser("eval", help="Run retrieval eval JSON")
    eval_parser.add_argument("file", type=Path, help="Path to eval JSON")
    eval_parser.set_defaults(func=cmd_eval)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
