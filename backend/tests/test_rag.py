from rag.chunking.chunker import chunk_blocks
from rag.pipeline.query import answer_question
from rag.schemas import ExtractedBlock, QueryRequest


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


def test_answer_question_without_database_url():
    request = QueryRequest(query="What is velocity?", grade=9, subject="Physics")
    response = answer_question(request)
    assert "configured" in response.answer.lower()
    assert response.model_used == "none"
