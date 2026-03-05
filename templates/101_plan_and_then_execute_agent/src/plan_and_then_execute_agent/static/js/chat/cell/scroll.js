/*
  목적: 채팅 메시지 영역의 자동 스크롤 동작을 제공한다.
  설명: 하단 근접 판별과 안전한 하단 고정 스크롤을 캡슐화한다.
  디자인 패턴: 유틸리티 모듈 패턴
  참조: js/chat/chat_cell.js, js/chat/cell/config.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  var config = window.App.chatCellConfig || {};
  var AUTO_SCROLL_BOTTOM_THRESHOLD_PX = Number(config.AUTO_SCROLL_BOTTOM_THRESHOLD_PX) || 24;

  function isNearBottom(container, thresholdPx) {
    var threshold = typeof thresholdPx === 'number' ? thresholdPx : AUTO_SCROLL_BOTTOM_THRESHOLD_PX;
    var distance = container.scrollHeight - container.clientHeight - container.scrollTop;
    return distance <= threshold;
  }

  function pinToBottom(container) {
    container.scrollTop = container.scrollHeight;
    if (typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(function () {
        container.scrollTop = container.scrollHeight;
        window.requestAnimationFrame(function () {
          container.scrollTop = container.scrollHeight;
        });
      });
    }
  }

  function scrollToBottom(container, force) {
    if (!force && !isNearBottom(container)) {
      return;
    }
    pinToBottom(container);
  }

  window.App.chatCellScroll = {
    isNearBottom: isNearBottom,
    scrollToBottom: scrollToBottom
  };
})();
