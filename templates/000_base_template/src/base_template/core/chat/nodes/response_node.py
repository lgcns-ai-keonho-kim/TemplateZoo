"""
목적: Chat Response 노드 조립체를 제공한다.
설명: 모델/클라이언트/노드를 모듈 레벨에서 선언해 그래프에서 바로 주입해 사용할 수 있게 한다.
디자인 패턴: 모듈 조립
참조: src/base_template/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations
import os
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from base_template.core.chat.prompts import CHAT_PROMPT
from base_template.integrations.llm import LLMClient
from base_template.shared.chat.nodes import LLMNode

_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", ""),
    api_key=SecretStr(
        os.getenv("OPENAI_API_KEY", "")
    ),
)


# NOTE: name은 로깅 구분용 식별자이다.
_llm_client = LLMClient(
    model=_model,
    name="chat-response-llm",
)

response_node = LLMNode(
    llm_client=_llm_client,
    node_name="response", # 스트림 이벤트의 node 필드 값
    prompt=CHAT_PROMPT, # 답변 정책/역할을 정의하는 시스템 프롬프트 템플릿
    output_key="assistant_message", # 이 노드 결과를 state에 기록할 키 (response 결과는 assistant_message)
)

__all__ = ["response_node"]
