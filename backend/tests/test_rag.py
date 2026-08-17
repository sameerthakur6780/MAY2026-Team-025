import rag.cache.redis_cache as redis_cache
import rag.config as rag_config
import rag.embedding.gemini_embedder as gemini_embedder
import rag.extraction.pdf_extractor as pdf_extractor
import rag.generation.answer_generator as answer_generator
import rag.pipeline.query as query_pipeline
import rag.store.supabase_store as supabase_store
from app.services import assistant_service
from rag.chunking.chunker import chunk_blocks
from pdfplumber.utils.exceptions import PdfminerException
from rag.generation.answer_generator import truncate_excerpt
from rag.generation.json_utils import extract_json_object
from rag.pipeline.query import answer_question
from rag.schemas import ExtractedBlock, QueryRequest, QueryResponse, RagAnswer


def test_collapse_repeated_tokens():
    raw = "TOMS TOMS TOMS TOMS AND AND AND AND M M M M M OLECULES"
    cleaned = pdf_extractor.collapse_repeated_tokens(raw)
    assert cleaned == "TOMS AND M OLECULES"


def test_is_numbered_list_detects_end_of_chapter_questions():
    text = (
        "5. Compare all the proposed models of an atom given in this chapter.\n"
        "6. Summarise the rules for writing of distribution of electrons.\n"
        "7. Define valency by taking examples of silicon and oxygen."
    )
    assert pdf_extractor.is_numbered_list(text)
    assert pdf_extractor._classify_block(text, None) == "exercise"


def test_extract_pdf_preserves_reading_order(monkeypatch):
    class FakeDoc:
        metadata = {"title": "Order Sample"}

        def close(self):
            return None

    page_chunks = [
        {
            "text": "Alpha comes first.\n\nBeta comes second.\n\nGamma comes third.",
            "page": 0,
        }
    ]
    monkeypatch.setattr(pdf_extractor.fitz, "open", lambda **_kwargs: FakeDoc())
    monkeypatch.setattr(pdf_extractor, "_markdown_page_chunks", lambda _doc: page_chunks)
    monkeypatch.setattr(pdf_extractor, "_extract_tables_fallback", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(pdf_extractor, "hash_pdf_bytes", lambda _data: "hash")

    result = pdf_extractor.extract_pdf(b"fake-pdf", title="Order Sample")
    joined = "\n".join(block.text for block in result.blocks)
    assert joined.index("Alpha") < joined.index("Beta") < joined.index("Gamma")


def test_chunk_blocks_preserves_input_order():
    blocks = [
        ExtractedBlock(text="Alpha paragraph.", content_type="explanation", page=1, chapter="Ch1", section="Sec"),
        ExtractedBlock(text="Beta paragraph.", content_type="explanation", page=1, chapter="Ch1", section="Sec"),
        ExtractedBlock(text="Gamma paragraph.", content_type="explanation", page=1, chapter="Ch1", section="Sec"),
    ]
    chunks = chunk_blocks(blocks, book_id="book-1", subject="Science", grade=9)
    assert chunks
    parent = chunks[0].parent_text
    assert parent.index("Alpha") < parent.index("Beta") < parent.index("Gamma")


def test_truncate_excerpt_stops_at_sentence_boundary():
    text = "First sentence here. Second sentence continues with many more words."
    excerpt = truncate_excerpt(text, limit=30)
    assert excerpt.endswith(".")
    assert "Second" not in excerpt


def test_retrieval_excludes_exercise_and_reference_content():
    assert "reference" in supabase_store._GROUNDING_CONTENT_FILTER
    assert "exercise" in supabase_store._GROUNDING_CONTENT_FILTER


def test_ask_assistant_profile_only(monkeypatch):
    monkeypatch.setattr(assistant_service, "_student_context", lambda _user_id: (9, "Grade 9"))
    monkeypatch.setattr(
        assistant_service,
        "answer_question",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("retrieval should be skipped")),
    )
    result = assistant_service.ask_assistant(1, "Which grade am I in?")
    assert result.model_used == "profile"
    assert "Grade 9" in result.answer


def test_ask_assistant_prepends_grade_for_combined_question(monkeypatch):
    monkeypatch.setattr(assistant_service, "_student_context", lambda _user_id: (9, "Grade 9"))
    monkeypatch.setattr(assistant_service, "_subject_name", lambda _subject, _query: "Physics")
    monkeypatch.setattr(assistant_service, "_infer_chapter_from_query", lambda _query: "Chapter 3")
    monkeypatch.setattr(
        assistant_service,
        "answer_question",
        lambda _request: QueryResponse(
            answer="Atomic models include Dalton, Thomson, and Rutherford models.",
            model_used="test-model",
        ),
    )
    result = assistant_service.ask_assistant(
        1,
        "Can you give the list of different Atomic models proposed in Physics chapter 3? And which grade Am i in?",
    )
    assert result.answer.startswith("You are in Grade 9.")
    assert "Atomic models include Dalton" in result.answer


def test_extract_json_object_handles_clean_and_fenced_json():
    assert extract_json_object('{"answer": "hello", "citations": []}') == {
        "answer": "hello",
        "citations": [],
    }
    fenced = '```json\n{"answer": "hello", "citations": []}\n```'
    assert extract_json_object(fenced) == {"answer": "hello", "citations": []}


def test_extract_json_object_handles_prose_prefix():
    raw = 'Here is the JSON:\n```json\n{"answer": "hello", "citations": []}\n```'
    assert extract_json_object(raw) == {"answer": "hello", "citations": []}


def test_extract_json_object_returns_none_for_invalid_json():
    assert extract_json_object("```json\n{\"answer\": \"The provided textbook excerpts") is None
    assert extract_json_object("") is None


def test_generate_answer_falls_back_to_extractive_on_parse_failure(monkeypatch):
    cfg = type("Config", (), {"generation_enabled": True})()
    monkeypatch.setattr(answer_generator, "get_rag_config", lambda: cfg)
    monkeypatch.setattr(
        answer_generator,
        "completion_with_fallback",
        lambda *_args, **_kwargs: (
            '```json\n{"answer": "The provided textbook excerpts do not contain',
            "test-model",
        ),
    )

    context_blocks = [
        {
            "book_id": "book-1",
            "chapter": "Laws of Motion",
            "section": "Third Law",
            "page_range": "12-13",
            "content_type": "explanation",
            "content": "Every action has an equal and opposite reaction.",
            "parent_text": "Every action has an equal and opposite reaction.",
        }
    ]
    result = answer_generator.generate_answer(
        "What is Newton's third law?",
        context_blocks,
        grade=9,
        subject="Physics",
    )

    assert "```json" not in result.answer
    assert "Every action has an equal and opposite reaction." in result.answer
    assert result.model_used == "retrieval-only"


def test_generate_answer_uses_llm_for_general_knowledge_when_no_hits(monkeypatch):
    cfg = type("Config", (), {"generation_enabled": True})()
    monkeypatch.setattr(answer_generator, "get_rag_config", lambda: cfg)
    calls = []

    def fake_completion(messages, **_kwargs):
        calls.append(messages)
        return (
            '{"answer": "This isn\'t covered in your textbook, but here\'s a general explanation: '
            'For every action there is an equal and opposite reaction.", "citations": []}',
            "test-model",
        )

    monkeypatch.setattr(answer_generator, "completion_with_fallback", fake_completion)

    result = answer_generator.generate_answer(
        "What is Newton's third law?",
        [],
        grade=9,
        subject="Physics",
    )

    assert calls
    assert result.answer.startswith("This isn't covered in your textbook")
    assert result.citations == []
    assert result.model_used == "test-model"


def test_cache_key_differs_by_chapter():
    key_a = redis_cache._cache_key("What is velocity?", grade=9, subject="Physics", chapter="Chapter 1")
    key_b = redis_cache._cache_key("What is velocity?", grade=9, subject="Physics", chapter="Chapter 2")
    key_none = redis_cache._cache_key("What is velocity?", grade=9, subject="Physics")

    assert key_a != key_b
    assert key_a != key_none


def test_chunk_blocks_deduplicates_and_skips_reference():
    blocks = [
        ExtractedBlock(text="Motion is change in position.", content_type="explanation", page=1, chapter="Motion", section="Intro"),
        ExtractedBlock(text="Motion is change in position.", content_type="explanation", page=1, chapter="Motion", section="Intro"),
        ExtractedBlock(text="References", content_type="reference", page=99, chapter="Back matter", section="References"),
    ]
    chunks = chunk_blocks(blocks, book_id="book-1", subject="Physics", grade=9)
    assert len(chunks) == 1
    assert chunks[0].subject == "Physics"
    assert chunks[0].grade == 9


def test_answer_question_without_database_url(monkeypatch):
    monkeypatch.setattr(query_pipeline, "get_rag_config", lambda: type("Config", (), {"database_url": ""})())

    request = QueryRequest(query="What is velocity?", grade=9, subject="Physics")
    response = answer_question(request)
    assert "configured" in response.answer.lower()
    assert response.model_used == "none"


def test_rag_database_url_derives_from_supabase_config(monkeypatch):
    monkeypatch.delenv("RAG_DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_POOLER_HOST", raising=False)
    monkeypatch.delenv("SUPABASE_DB_REGION", raising=False)
    monkeypatch.setenv("PROJECT_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("DB_PASSWORD", "pass word")
    rag_config.get_rag_config.cache_clear()

    cfg = rag_config.get_rag_config()

    assert cfg.database_url == "postgresql://postgres:pass%20word@db.project-ref.supabase.co:5432/postgres"
    rag_config.get_rag_config.cache_clear()


def test_rag_database_url_can_use_supabase_pooler_region(monkeypatch):
    monkeypatch.delenv("RAG_DATABASE_URL", raising=False)
    monkeypatch.setenv("PROJECT_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("DB_PASSWORD", "pass word")
    monkeypatch.setenv("SUPABASE_DB_REGION", "ap-south-1")
    rag_config.get_rag_config.cache_clear()

    cfg = rag_config.get_rag_config()

    assert (
        cfg.database_url
        == "postgresql://postgres.project-ref:pass%20word@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    )
    rag_config.get_rag_config.cache_clear()


def test_rag_database_url_explicit_override_wins(monkeypatch):
    monkeypatch.setenv("RAG_DATABASE_URL", "postgresql://postgres.example/pooler")
    monkeypatch.setenv("PROJECT_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("DB_PASSWORD", "password")
    rag_config.get_rag_config.cache_clear()

    cfg = rag_config.get_rag_config()

    assert cfg.database_url == "postgresql://postgres.example/pooler"
    rag_config.get_rag_config.cache_clear()


def test_embed_texts_requests_configured_dimensions(monkeypatch):
    calls = {}
    cfg = type(
        "Config",
        (),
        {
            "embedding_model": "gemini/gemini-embedding-001",
            "embedding_dimensions": 768,
        },
    )()

    def fake_embedding(**kwargs):
        calls.update(kwargs)
        return type("Response", (), {"data": [{"embedding": [0.1]}, {"embedding": [0.2]}]})()

    monkeypatch.setattr(gemini_embedder, "_ensure_api_key", lambda: None)
    monkeypatch.setattr(gemini_embedder, "get_rag_config", lambda: cfg)
    monkeypatch.setattr(gemini_embedder.litellm, "embedding", fake_embedding)

    assert gemini_embedder.embed_texts(["first", "second"]) == [[0.1], [0.2]]
    assert calls["model"] == "gemini/gemini-embedding-001"
    assert calls["input"] == ["first", "second"]
    assert calls["dimensions"] == 768


def test_extract_pdf_skips_pdfplumber_table_failures(monkeypatch):
    import fitz

    def raise_pdfminer_exception(_stream):
        raise PdfminerException(Exception("Unsupported predictor: 2"))

    monkeypatch.setattr(pdf_extractor.pdfplumber, "open", raise_pdfminer_exception)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Chapter 4\n\nCharged particles in matter.")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = pdf_extractor.extract_pdf(pdf_bytes, title="Physics Sample")

    assert any("Charged particles" in block.text for block in result.blocks)


def test_upstash_rest_cache_backend(monkeypatch):
    store = {}

    monkeypatch.setattr(redis_cache, "_redis_client", lambda: None)
    monkeypatch.setattr(
        redis_cache,
        "get_rag_config",
        lambda: type(
            "Config",
            (),
            {
                "cache_ttl_seconds": 60,
                "upstash_redis_rest_url": "https://fake-upstash.test",
                "upstash_redis_rest_token": "fake-token",
            },
        )(),
    )

    def fake_upstash_command(command, *args):
        if command == "SETEX":
            key, _ttl, value = args
            store[key] = value
            return "OK"
        if command == "GET":
            return store.get(args[0])
        if command == "KEYS":
            return list(store)
        return None

    monkeypatch.setattr(redis_cache, "_upstash_command", fake_upstash_command)

    answer = RagAnswer(answer="Velocity is speed with direction.", model_used="test-model")
    redis_cache.set_cached_answer("What is velocity?", answer, grade=9, subject="Physics")

    cached = redis_cache.get_cached_answer("What is velocity?", grade=9, subject="Physics")
    assert cached is not None
    assert cached.answer == answer.answer
    assert redis_cache.cache_stats() == {"backend": "upstash-rest", "entries": 1}
