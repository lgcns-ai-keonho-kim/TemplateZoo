/*
  목적: 개별 채팅 셀 UI 및 API 연동 동작을 처리한다.
  설명: 사용자 입력, 상태 전이, 셀 라이프사이클 제어를 담당하며 세부 기능은 하위 모듈에 위임한다.
  디자인 패턴: 상태 캡슐화 컴포넌트 + 조합(Composition)
  참조: js/chat/cell/config.js, js/chat/cell/scroll.js, js/chat/cell/references.js, js/chat/cell/stream.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.chatCell = window.App.chatCell || {};

  var escapeHtml = window.App.utils.escapeHtml;
  var config = window.App.chatCellConfig || {};
  var scrollUtil = window.App.chatCellScroll;
  var referencesUtil = window.App.chatCellReferences;
  var streamUtil = window.App.chatCellStream;

  if (!scrollUtil || !referencesUtil || !streamUtil) {
    throw new Error('chat_cell 의존 모듈이 로드되지 않았습니다. index.html의 script 순서를 확인하세요.');
  }

  var DEFAULT_CONTEXT_WINDOW = Number(config.DEFAULT_CONTEXT_WINDOW) || 20;
  var CHAT_CELL_BUILD_TAG = String(config.CHAT_CELL_BUILD_TAG || 'chat-cell-unknown');
  var AUTO_SCROLL_DETECT_THRESHOLD_PX = Number(config.AUTO_SCROLL_DETECT_THRESHOLD_PX) || 72;
  var PROGRAMMATIC_SCROLL_GUARD_MS = Number(config.PROGRAMMATIC_SCROLL_GUARD_MS) || 240;
  var SCROLL_MODE_FOLLOWING = String(config.SCROLL_MODE_FOLLOWING || 'FOLLOWING');
  var SCROLL_MODE_PAUSED_BY_USER = String(config.SCROLL_MODE_PAUSED_BY_USER || 'PAUSED_BY_USER');

  console.info('[ui] chat_cell 로드:', CHAT_CELL_BUILD_TAG);

  window.App.chatCell.create = function (cellId, title, options) {
    var presenter = window.App.chatPresenter;
    if (!presenter || typeof presenter.renderStreamingHtml !== 'function') {
      console.warn('[ui] chat_presenter 스크립트 버전이 맞지 않습니다. 강력 새로고침(Ctrl+Shift+R)을 권장합니다.');
    } else if (typeof presenter.renderRealtimeStreamingHtml !== 'function') {
      console.warn('[ui] renderRealtimeStreamingHtml 미탑재 버전입니다. fallback 렌더를 사용합니다.');
    }

    var seed = options || {};
    var state = {
      id: cellId,
      sessionId: String(seed.sessionId || cellId),
      activeRequestId: '',
      isSending: false,
      destroyed: false,
      finalized: false,
      activeBubble: null,
      activeMessageNode: null,
      streamHandle: null,
      tokenBuffer: '',
      receivedText: '',
      references: [],
      timers: [],
      scrollMode: SCROLL_MODE_FOLLOWING,
      programmaticScrollUntil: 0
    };

    var cell = window.App.utils.createEl('section', 'chat-cell');
    cell.setAttribute('data-cell-id', cellId);

    var header = window.App.utils.createEl('div', 'chat-cell__header');
    var headerTitle = window.App.utils.createEl('div', 'chat-cell__title');
    headerTitle.textContent = title;
    header.appendChild(headerTitle);

    var messages = window.App.utils.createEl('div', 'chat-cell__messages');

    var status = window.App.utils.createEl('div', 'chat-cell__status');
    var statusPill = window.App.utils.createEl('span', 'status-pill');
    statusPill.textContent = 'QUEUE';
    var statusText = window.App.utils.createEl('span', 'status-text');
    statusText.textContent = '대기 중';
    var spinner = window.App.utils.createEl('span', 'spinner is-hidden');
    status.appendChild(statusPill);
    status.appendChild(statusText);
    status.appendChild(spinner);

    var composer = window.App.utils.createEl('div', 'chat-cell__composer');
    var input = window.App.utils.createEl('textarea', 'composer-input');
    input.placeholder = '메시지를 입력하세요 (Enter 전송, Shift+Enter 줄바꿈)';
    var actions = window.App.utils.createEl('div', 'composer-actions');
    var sendBtn = window.App.utils.createEl('button', 'btn-primary btn-icon-round');
    sendBtn.type = 'button';
    sendBtn.setAttribute('title', '보내기');
    sendBtn.setAttribute('aria-label', '보내기');
    var sendIcon = window.App.utils.createEl('img', 'icon');
    sendIcon.setAttribute('src', 'asset/icons/send.svg');
    sendIcon.setAttribute('alt', '');
    sendBtn.appendChild(sendIcon);

    var stopBtn = window.App.utils.createEl('button', 'btn-secondary is-hidden btn-disabled');
    stopBtn.type = 'button';
    stopBtn.textContent = '중지';

    actions.appendChild(sendBtn);
    actions.appendChild(stopBtn);
    composer.appendChild(input);

    var disclaimer = window.App.utils.createEl('div', 'composer-disclaimer');
    var disclaimerIcon = window.App.utils.createEl('img', 'disclaimer-icon');
    disclaimerIcon.setAttribute('src', 'asset/icons/priority_high.svg');
    disclaimerIcon.setAttribute('alt', '');
    var disclaimerText = document.createElement('span');
    disclaimerText.textContent = 'AI의 응답은 부정확할 수 있습니다.';
    disclaimer.appendChild(disclaimerIcon);
    disclaimer.appendChild(disclaimerText);

    var footer = window.App.utils.createEl('div', 'composer-footer');
    footer.appendChild(disclaimer);
    footer.appendChild(actions);
    composer.appendChild(footer);

    cell.appendChild(header);
    cell.appendChild(messages);
    cell.appendChild(status);
    cell.appendChild(composer);

    function isAutoScrollFollowing() {
      return state.scrollMode === SCROLL_MODE_FOLLOWING;
    }

    function addTimer(callback, ms) {
      if (state.destroyed) {
        return null;
      }
      var timer = setTimeout(function () {
        if (state.destroyed) {
          return;
        }
        callback();
      }, ms);
      state.timers.push(timer);
      return timer;
    }

    function clearTimers() {
      state.timers.forEach(function (timerId) {
        clearTimeout(timerId);
      });
      state.timers = [];
    }

    function detachStream() {
      if (state.streamHandle && typeof state.streamHandle.close === 'function') {
        state.streamHandle.close();
      }
      state.streamHandle = null;
    }

    function hideStatusLater(ms) {
      addTimer(function () {
        status.classList.remove('is-visible');
      }, ms);
    }

    function setRuntimeInfo(node, metadata) {
      if (!presenter || typeof presenter.setRuntimeInfo !== 'function') {
        return;
      }
      presenter.setRuntimeInfo(status, node, metadata);
    }

    function updateHistory(preview) {
      if (window.App.app && window.App.app.updateHistory) {
        window.App.app.updateHistory(cellId, headerTitle.textContent, preview);
      }
    }

    function scrollMessagesToBottom(force) {
      if (!force && !isAutoScrollFollowing()) {
        return;
      }
      state.programmaticScrollUntil = Date.now() + PROGRAMMATIC_SCROLL_GUARD_MS;
      scrollUtil.scrollToBottom(messages, true);
    }

    function addMessage(role, text) {
      var created = presenter.createMessageNode(role, presenter.renderMessageHtml(text));
      messages.appendChild(created.message);
      scrollMessagesToBottom(isAutoScrollFollowing());
      return created;
    }

    function addUserMessage(text) {
      addMessage('user', text);
      updateHistory(text);
    }

    function addAssistantPlaceholder() {
      var created = presenter.createMessageNode('assistant', '<div class="markdown"></div>');
      messages.appendChild(created.message);
      scrollMessagesToBottom(isAutoScrollFollowing());
      return created;
    }

    function renderStreamingBubble() {
      if (!state.activeBubble) {
        return;
      }
      var renderRealtime = presenter && typeof presenter.renderRealtimeStreamingHtml === 'function'
        ? presenter.renderRealtimeStreamingHtml
        : null;
      var renderFallback = presenter && typeof presenter.renderStreamingHtml === 'function'
        ? presenter.renderStreamingHtml
        : null;

      if (renderRealtime) {
        state.activeBubble.innerHTML = renderRealtime(state.receivedText, true);
      } else if (renderFallback) {
        state.activeBubble.innerHTML = renderFallback(state.receivedText, true);
      } else {
        state.activeBubble.textContent = state.receivedText;
      }
      scrollMessagesToBottom(isAutoScrollFollowing());
    }

    function renderFinalBubble(text) {
      if (!state.activeBubble) {
        return;
      }
      if (presenter && typeof presenter.renderStreamingHtml === 'function') {
        state.activeBubble.innerHTML = presenter.renderStreamingHtml(text, false);
      } else {
        state.activeBubble.textContent = String(text || '');
      }
      scrollMessagesToBottom(isAutoScrollFollowing());
    }

    function renderReferencesCarousel(references) {
      referencesUtil.renderCarousel(state.activeMessageNode, references);
    }

    function finishSending() {
      detachStream();
      presenter.setSendingState(state, false, sendBtn, stopBtn, input);
      state.activeBubble = null;
      state.activeMessageNode = null;
      state.receivedText = '';
      state.references = [];
      state.activeRequestId = '';
      setRuntimeInfo('', null);
    }

    function finalizeSuccess(finalText) {
      if (state.finalized || state.destroyed) {
        return;
      }
      state.finalized = true;
      var resolvedText = typeof finalText === 'string'
        ? finalText
        : (state.receivedText || state.tokenBuffer || '');
      renderFinalBubble(resolvedText);
      renderReferencesCarousel(state.references);
      updateHistory(presenter.firstLine(resolvedText));
      presenter.setStatus(status, '완료', false, 'DONE', false);
      finishSending();
      hideStatusLater(1000);
    }

    function finalizeError(message) {
      if (state.finalized || state.destroyed) {
        return;
      }
      state.finalized = true;
      var safeMessage = message && String(message).trim() ? String(message).trim() : '응답 생성에 실패했습니다.';
      if (state.activeBubble && !state.tokenBuffer) {
        state.activeBubble.innerHTML = '<p>' + escapeHtml('오류: ' + safeMessage) + '</p>';
      }
      presenter.setStatus(status, '실패: ' + safeMessage, false, 'FAIL', false);
      finishSending();
      hideStatusLater(2000);
    }

    function connectStream(userMessage) {
      streamUtil.connect({
        state: state,
        presenter: presenter,
        statusEl: status,
        userMessage: userMessage,
        contextWindow: DEFAULT_CONTEXT_WINDOW,
        detachStream: detachStream,
        setRuntimeInfo: setRuntimeInfo,
        renderStreamingBubble: renderStreamingBubble,
        finalizeSuccess: finalizeSuccess,
        finalizeError: finalizeError,
        parseReferences: referencesUtil.parse
      });
    }

    function adjustTextareaHeight() {
      var maxHeight = 220;
      input.style.height = 'auto';
      var nextHeight = Math.min(input.scrollHeight, maxHeight);
      input.style.height = nextHeight + 'px';
    }

    function setCellActive() {
      var activeCells = document.querySelectorAll('.chat-cell.is-active');
      activeCells.forEach(function (activeCell) {
        if (activeCell !== cell) {
          activeCell.classList.remove('is-active');
        }
      });
      cell.classList.add('is-active');
    }

    function handleStop() {
      if (!state.isSending) {
        return;
      }
      clearTimers();
      detachStream();
      if (state.activeBubble) {
        var caret = state.activeBubble.querySelector('.typing-caret');
        if (caret) {
          caret.remove();
        }
      }
      state.finalized = true;
      presenter.setSendingState(state, false, sendBtn, stopBtn, input);
      state.activeBubble = null;
      state.activeMessageNode = null;
      state.references = [];
      state.activeRequestId = '';
      setRuntimeInfo('', null);
      status.classList.add('is-visible');
      presenter.setStatus(status, '수신 중지', false, 'STOP', false);
      hideStatusLater(1200);
    }

    function handleSend() {
      var text = input.value.trim();
      if (!text || state.isSending || state.destroyed) {
        return;
      }

      clearTimers();
      input.value = '';
      adjustTextareaHeight();
      state.scrollMode = SCROLL_MODE_FOLLOWING;
      addUserMessage(text);
      presenter.setSendingState(state, true, sendBtn, stopBtn, input);
      status.classList.add('is-visible');
      presenter.setStatus(status, '요청 전송중...', true, 'STREAM', true);

      var assistantMessage = addAssistantPlaceholder();
      state.activeMessageNode = assistantMessage.message;
      state.activeBubble = assistantMessage.bubble.querySelector('.markdown');
      state.tokenBuffer = '';
      state.receivedText = '';
      state.references = [];
      state.finalized = false;
      renderStreamingBubble();

      connectStream(text);
    }

    function onSendClick() {
      handleSend();
    }

    function onStopClick() {
      handleStop();
    }

    function onInputKeyDown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    }

    function onInputFocus() {
      setCellActive();
    }

    function onInputBlur() {
      cell.classList.remove('is-active');
    }

    function onInput() {
      adjustTextareaHeight();
    }

    function onMessagesScroll() {
      if (Date.now() < state.programmaticScrollUntil) {
        return;
      }
      if (scrollUtil.isNearBottom(messages, AUTO_SCROLL_DETECT_THRESHOLD_PX)) {
        state.scrollMode = SCROLL_MODE_FOLLOWING;
        return;
      }
      state.scrollMode = SCROLL_MODE_PAUSED_BY_USER;
    }

    function renderSeedMessages() {
      var initial = Array.isArray(seed.initialMessages) ? seed.initialMessages : [];
      initial.forEach(function (item) {
        var role = presenter.normalizeRole(item && item.role);
        var content = item && typeof item.content === 'string' ? item.content : '';
        addMessage(role, content);
      });
      state.scrollMode = SCROLL_MODE_FOLLOWING;
      scrollMessagesToBottom(true);
    }

    function destroy() {
      if (state.destroyed) {
        return;
      }
      state.destroyed = true;
      state.finalized = true;
      clearTimers();
      detachStream();
      presenter.setSendingState(state, false, sendBtn, stopBtn, input);
      state.activeBubble = null;
      state.activeMessageNode = null;
      state.references = [];

      sendBtn.removeEventListener('click', onSendClick);
      stopBtn.removeEventListener('click', onStopClick);
      input.removeEventListener('keydown', onInputKeyDown);
      input.removeEventListener('focus', onInputFocus);
      input.removeEventListener('blur', onInputBlur);
      input.removeEventListener('input', onInput);
      messages.removeEventListener('scroll', onMessagesScroll);
    }

    sendBtn.addEventListener('click', onSendClick);
    stopBtn.addEventListener('click', onStopClick);
    input.addEventListener('keydown', onInputKeyDown);
    input.addEventListener('focus', onInputFocus);
    input.addEventListener('blur', onInputBlur);
    input.addEventListener('input', onInput);
    messages.addEventListener('scroll', onMessagesScroll);

    renderSeedMessages();

    return {
      element: cell,
      destroy: destroy
    };
  };
})();
