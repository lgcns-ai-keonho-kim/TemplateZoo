"""
목적: Safeguard 결과 라우팅 노드 조립체를 제공한다.
설명: BranchNode를 직접 조립해 safeguard_result를 response/blocked 분기로 변환한다.
디자인 패턴: 모듈 조립
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from rag_chatbot.shared.chat.nodes import BranchNode

# NOTE:
# BranchNode 인자 설명(이 조합이 실제 사용 예시):

safeguard_route_node = BranchNode(
    selector_key="safeguard_result", # safeguard 노드 결과를 읽어올 state 키.
    branch_map={"PASS": "response"}, # selector가 PASS일 때만 response로 보낸다. 나머지는 default_branch 사용.
    default_branch="blocked", # PASS가 아닌 모든 경우 blocked 분기로 보낸다.
    output_key="safeguard_route", # conditional edge에서 읽을 분기 키를 state에 저장한다.
    aliases={
        "PROMPT_INJETION": "PROMPT_INJECTION",
        "PROMPT_INJECTION": "PROMPT_INJECTION",
    }, # 과거 오타 토큰(PROMPT_INJETION)을 내부 표준(PROMPT_INJECTION)으로 교정한다.
    normalize_case=True, # 대소문자 변형("pass", "Pass")이 와도 PASS로 정규화.
    allowed_selectors={"PASS", "PII", "HARMFUL", "PROMPT_INJECTION"}, # 허용 가능한 safeguard 반환값 집합(set).
    fallback_selector="HARMFUL", # 허용 집합 밖의 예측치가 오면 HARMFUL로 강제.
    write_normalized_to="safeguard_result", # 교정된 selector를 다시 safeguard_result에 써서 downstream(MessageNode)에서 재사용.
)

__all__ = ["safeguard_route_node"]
