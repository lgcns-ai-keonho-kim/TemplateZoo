/*
  목적: 채팅 셀 공통 상수 구성을 제공한다.
  설명: 스트림/스크롤/상태 전이에 필요한 기본 상수를 단일 위치에서 관리한다.
  디자인 패턴: 설정 객체 패턴
  참조: js/chat/chat_cell.js, js/chat/cell/scroll.js, js/chat/cell/stream.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  window.App.chatCellConfig = {
    DEFAULT_CONTEXT_WINDOW: 20,
    CHAT_CELL_BUILD_TAG: 'chat-cell-20260224-split-v1',
    AUTO_SCROLL_BOTTOM_THRESHOLD_PX: 24,
    AUTO_SCROLL_DETECT_THRESHOLD_PX: 72,
    PROGRAMMATIC_SCROLL_GUARD_MS: 240,
    SCROLL_MODE_FOLLOWING: 'FOLLOWING',
    SCROLL_MODE_PAUSED_BY_USER: 'PAUSED_BY_USER'
  };
})();
