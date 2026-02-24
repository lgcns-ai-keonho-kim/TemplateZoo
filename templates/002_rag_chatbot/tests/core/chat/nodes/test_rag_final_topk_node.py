"""
목적: RAG 최종 top-k 노드 동작을 검증한다.
설명: score 내림차순 정렬 후 설정된 top-k로 절단되는지 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_final_topk_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.rag_final_topk_node import rag_final_topk_node


def test_rag_final_topk_sorts_and_limits() -> None:
    """score 기준 내림차순 정렬과 top-k 절단이 적용되어야 한다."""

    docs = []
    for index in range(10):
        docs.append(
            {
                "chunk_id": f"c{index}",
                "index": index,
                "file_name": f"f{index}.md",
                "file_path": f"/f{index}.md",
                "body": f"body-{index}",
                "metadata": {"page_num": index},
                "score": float(index),
                "source": "body",
            }
        )

    output = rag_final_topk_node.run({"rag_file_page_deduped_docs": docs})
    final_docs = output["rag_filtered_docs"]

    assert len(final_docs) == 8
    assert final_docs[0]["chunk_id"] == "c9"
    assert final_docs[-1]["chunk_id"] == "c2"
