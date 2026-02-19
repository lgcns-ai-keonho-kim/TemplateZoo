/*
  목적: 개별 채팅 셀 UI 및 API 연동 동작을 처리한다.
  설명: 사용자 입력과 단일 SSE 스트림 응답 처리, 리소스 정리를 구현한다.
  디자인 패턴: 상태 캡슐화 컴포넌트
  참조: js/chat/api_transport.js, js/chat/chat_presenter.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.chatCell = window.App.chatCell || {};

  var escapeHtml = window.App.utils.escapeHtml;
  var DEFAULT_CONTEXT_WINDOW = 20;
  var AUTO_SCROLL_BOTTOM_THRESHOLD_PX = 24;
  var AUTO_SCROLL_DETECT_THRESHOLD_PX = 72;
  var PROGRAMMATIC_SCROLL_GUARD_MS = 240;
  var SCROLL_MODE_FOLLOWING = 'FOLLOWING';
  var SCROLL_MODE_PAUSED_BY_USER = 'PAUSED_BY_USER';

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
      streamHandle: null,
      tokenBuffer: '',
      receivedText: '',
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

    function scrollMessagesToBottom(force) {
      if (!force && !isAutoScrollFollowing()) {
        return;
      }
      state.programmaticScrollUntil = Date.now() + PROGRAMMATIC_SCROLL_GUARD_MS;
      scrollToBottom(messages, true);
    }

    function finishSending() {
      detachStream();
      presenter.setSendingState(state, false, sendBtn, stopBtn, input);
      state.activeBubble = null;
      state.receivedText = '';
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
      if (state.finalized || state.destroyed || !state.isSending) {
        return;
      }
      detachStream();
      presenter.setStatus(status, '스트림 연결중', true, 'STREAM', true);
      state.streamHandle = window.App.apiTransport.streamMessage(state.sessionId, userMessage, DEFAULT_CONTEXT_WINDOW, {
        onQueued: function (queued) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          state.activeRequestId = queued && queued.request_id ? String(queued.request_id) : '';
          var queuedSessionId = queued && queued.session_id ? String(queued.session_id) : '';
          if (queuedSessionId) {
            state.sessionId = queuedSessionId;
          }
          presenter.setStatus(status, '작업 큐 적재 완료', true, 'QUEUE', true);
          setRuntimeInfo('queue', null);
        },
        onOpen: function () {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          presenter.setStatus(status, '응답 생성중', true, 'STREAM', true);
        },
        onEvent: function (payload) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          var eventType = payload && payload.type ? String(payload.type) : '';
          var eventRequestId = payload && payload.request_id ? String(payload.request_id) : '';
          var eventNode = payload && payload.node ? String(payload.node) : 'unknown';
          var eventMetadata = payload && payload.metadata && typeof payload.metadata === 'object'
            ? payload.metadata
            : null;
          if (state.activeRequestId && eventRequestId && state.activeRequestId !== eventRequestId) {
            return;
          }
          setRuntimeInfo(eventNode, eventMetadata);
          if (eventType === 'start') {
            presenter.setStatus(status, '응답 생성중 [' + eventNode + ']', true, 'STREAM', true);
            return;
          }
          if (eventType === 'token') {
            var chunk = payload && typeof payload.content === 'string' ? payload.content : '';
            if (!chunk) {
              return;
            }
            if (eventNode === 'response') {
              state.tokenBuffer += chunk;
              state.receivedText = state.tokenBuffer;
              renderStreamingBubble();
              presenter.setStatus(status, '응답 수신중 [' + eventNode + ']', true, 'STREAM', true);
              return;
            }
            presenter.setStatus(status, '노드 처리중 [' + eventNode + ']', true, 'STREAM', true);
            return;
          }
          if (eventType === 'error') {
            finalizeError(payload && payload.error_message ? payload.error_message : null);
            return;
          }
          if (eventType === 'done') {
            var doneStatus = payload && payload.status ? String(payload.status) : '';
            if (doneStatus === 'FAILED') {
              finalizeError(payload && payload.error_message ? payload.error_message : '응답 생성에 실패했습니다.');
              return;
            }
            var doneContent = payload && typeof payload.content === 'string' ? payload.content : '';
            var doneText = doneContent && doneContent.trim()
              ? doneContent
              : (state.tokenBuffer && state.tokenBuffer.trim() ? state.tokenBuffer : '');
            if (doneText) {
              state.tokenBuffer = doneText;
              state.receivedText = doneText;
              renderStreamingBubble();
              finalizeSuccess(doneText);
              return;
            }
            finalizeSuccess(state.tokenBuffer || '');
          }
        },
        onError: function (error) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          if (state.tokenBuffer && state.tokenBuffer.trim()) {
            finalizeSuccess(state.tokenBuffer);
            return;
          }
          finalizeError(error && error.message ? error.message : '스트림 연결에 실패했습니다.');
        }
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
      state.activeBubble = assistantMessage.bubble.querySelector('.markdown');
      state.tokenBuffer = '';
      state.receivedText = '';
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
      if (isNearBottom(messages, AUTO_SCROLL_DETECT_THRESHOLD_PX)) {
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
