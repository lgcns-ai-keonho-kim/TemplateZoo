/*
  목적: 개별 채팅 셀 UI 및 API 연동 동작을 처리한다.
  설명: 사용자 입력, 큐 등록, SSE 스트림, 오류 복구, 리소스 정리를 구현한다.
  디자인 패턴: 상태 캡슐화 컴포넌트
  참조: js/chat/api_transport.js, js/chat/chat_presenter.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.chatCell = window.App.chatCell || {};

  var escapeHtml = window.App.utils.escapeHtml;
  var DEFAULT_CONTEXT_WINDOW = 20;
  var RESULT_POLL_INTERVAL_MS = 500;
  var MAX_RESULT_POLL_COUNT = 1000;
  var MAX_STREAM_RETRY_COUNT = 3;
  var STREAM_RETRY_DELAYS_MS = [400, 800, 1200];
  var TYPEWRITER_MIN_CPS = 55;
  var TYPEWRITER_MAX_CPS = 900;
  var TYPEWRITER_TARGET_DRAIN_SECONDS = 2.2;
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

  function pickStreamRetryDelay(retryCount) {
    var index = Math.max(0, Math.min(retryCount - 1, STREAM_RETRY_DELAYS_MS.length - 1));
    return STREAM_RETRY_DELAYS_MS[index];
  }

  window.App.chatCell.create = function (cellId, title, options) {
    var presenter = window.App.chatPresenter;
    var seed = options || {};
    var state = {
      id: cellId,
      sessionId: String(seed.sessionId || cellId),
      isSending: false,
      destroyed: false,
      finalized: false,
      activeBubble: null,
      streamHandle: null,
      currentTaskId: null,
      tokenBuffer: '',
      receivedText: '',
      visibleText: '',
      streamRetryCount: 0,
      resultPollCount: 0,
      timers: [],
      scrollMode: SCROLL_MODE_FOLLOWING,
      programmaticScrollUntil: 0,
      doneEventReceived: false,
      pendingDoneText: '',
      typewriterFrameId: null,
      lastTypewriterFrameMs: 0,
      streamingTextElement: null,
      streamingCaretElement: null
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
      cancelTypewriterFrame();
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

    function cancelTypewriterFrame() {
      if (state.typewriterFrameId !== null && typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(state.typewriterFrameId);
      }
      state.typewriterFrameId = null;
      state.lastTypewriterFrameMs = 0;
    }

    function pickTypewriterCharsPerSecond(backlog) {
      var target = Math.ceil(backlog / TYPEWRITER_TARGET_DRAIN_SECONDS);
      var bounded = Math.max(TYPEWRITER_MIN_CPS, Math.min(TYPEWRITER_MAX_CPS, target));
      return bounded;
    }

    function ensureStreamingElements() {
      if (!state.activeBubble) {
        return;
      }
      if (
        state.streamingTextElement &&
        state.streamingCaretElement &&
        state.streamingTextElement.parentNode === state.activeBubble &&
        state.streamingCaretElement.parentNode === state.activeBubble
      ) {
        return;
      }
      state.activeBubble.innerHTML = '';
      state.streamingTextElement = window.App.utils.createEl('div', 'streaming-text');
      state.streamingTextElement.textContent = state.visibleText;
      state.streamingCaretElement = window.App.utils.createEl('span', 'typing-caret');
      state.activeBubble.appendChild(state.streamingTextElement);
      state.activeBubble.appendChild(state.streamingCaretElement);
    }

    function renderStreamingBubble() {
      if (!state.activeBubble) {
        return;
      }
      ensureStreamingElements();
      if (!state.streamingTextElement) {
        return;
      }
      state.streamingTextElement.textContent = state.visibleText;
      scrollMessagesToBottom(isAutoScrollFollowing());
    }

    function renderFinalBubble(text) {
      if (!state.activeBubble) {
        return;
      }
      state.streamingTextElement = null;
      state.streamingCaretElement = null;
      state.activeBubble.innerHTML = presenter.renderStreamingHtml(text, false);
      scrollMessagesToBottom(isAutoScrollFollowing());
    }

    function scrollMessagesToBottom(force) {
      if (!force && !isAutoScrollFollowing()) {
        return;
      }
      state.programmaticScrollUntil = Date.now() + PROGRAMMATIC_SCROLL_GUARD_MS;
      scrollToBottom(messages, true);
    }

    function handleTypewriterFrame(timestamp) {
      state.typewriterFrameId = null;
      if (state.finalized || state.destroyed || !state.isSending || !state.activeBubble) {
        state.lastTypewriterFrameMs = 0;
        return;
      }

      var previousTs = state.lastTypewriterFrameMs || timestamp;
      var elapsedMs = Math.max(0, timestamp - previousTs);
      state.lastTypewriterFrameMs = timestamp;

      var backlog = state.receivedText.length - state.visibleText.length;
      if (backlog > 0) {
        var cps = pickTypewriterCharsPerSecond(backlog);
        var step = Math.max(1, Math.floor((cps * elapsedMs) / 1000));
        var nextLength = Math.min(state.receivedText.length, state.visibleText.length + step);
        state.visibleText = state.receivedText.slice(0, nextLength);
        renderStreamingBubble();
      }

      if (state.doneEventReceived && state.visibleText.length >= state.receivedText.length) {
        finalizeSuccess(state.pendingDoneText || state.receivedText);
        return;
      }

      if (state.receivedText.length > state.visibleText.length || state.doneEventReceived) {
        state.typewriterFrameId = window.requestAnimationFrame(handleTypewriterFrame);
      } else {
        state.lastTypewriterFrameMs = 0;
      }
    }

    function startTypewriterLoop() {
      if (state.typewriterFrameId !== null) {
        return;
      }
      if (typeof window.requestAnimationFrame !== 'function') {
        renderStreamingBubble();
        if (state.doneEventReceived && state.visibleText.length >= state.receivedText.length) {
          finalizeSuccess(state.pendingDoneText || state.receivedText);
        }
        return;
      }
      state.typewriterFrameId = window.requestAnimationFrame(handleTypewriterFrame);
    }

    function finishSending() {
      cancelTypewriterFrame();
      detachStream();
      presenter.setSendingState(state, false, sendBtn, stopBtn, input);
      state.currentTaskId = null;
      state.activeBubble = null;
      state.receivedText = '';
      state.visibleText = '';
      state.doneEventReceived = false;
      state.pendingDoneText = '';
      state.streamingTextElement = null;
      state.streamingCaretElement = null;
    }

    function finalizeSuccess(finalText) {
      if (state.finalized || state.destroyed) {
        return;
      }
      state.finalized = true;
      var resolvedText = typeof finalText === 'string'
        ? finalText
        : (state.pendingDoneText || state.receivedText || state.tokenBuffer || '');
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
        state.streamingTextElement = null;
        state.streamingCaretElement = null;
      }
      presenter.setStatus(status, '실패: ' + safeMessage, false, 'FAIL', false);
      finishSending();
      hideStatusLater(2000);
    }

    function scheduleResultPoll(lastError) {
      if (state.finalized || state.destroyed || !state.isSending) {
        return;
      }
      state.resultPollCount += 1;
      if (state.resultPollCount > MAX_RESULT_POLL_COUNT) {
        if (state.tokenBuffer && state.tokenBuffer.trim()) {
          finalizeSuccess(state.tokenBuffer);
          return;
        }
        var timeoutMessage = lastError && lastError.message
          ? lastError.message
          : '결과 확정 대기 시간이 초과되었습니다.';
        finalizeError(timeoutMessage);
        return;
      }
      addTimer(function () {
        finalizeFromResult();
      }, RESULT_POLL_INTERVAL_MS);
    }

    function finalizeFromResult() {
      var taskId = state.currentTaskId;
      if (!taskId) {
        if (state.tokenBuffer) {
          finalizeSuccess(state.tokenBuffer);
          return;
        }
        finalizeError('태스크 식별자를 찾을 수 없습니다.');
        return;
      }

      window.App.apiTransport
        .getTaskResult(state.sessionId, taskId)
        .then(function (result) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          var currentStatus = result && result.status ? String(result.status) : '';
          if (currentStatus === 'FAILED') {
            finalizeError(result.error_message || '응답 생성에 실패했습니다.');
            return;
          }
          if (currentStatus !== 'COMPLETED') {
            scheduleResultPoll();
            return;
          }

          state.resultPollCount = 0;
          var finalText = state.tokenBuffer;
          if (
            result &&
            result.assistant_message &&
            typeof result.assistant_message.content === 'string' &&
            result.assistant_message.content.trim()
          ) {
            finalText = result.assistant_message.content;
          }
          if (finalText && finalText.trim()) {
            if (!state.tokenBuffer || finalText.indexOf(state.tokenBuffer) === 0) {
              state.tokenBuffer = finalText;
            }
            if (!state.receivedText || finalText.indexOf(state.receivedText) === 0) {
              state.receivedText = finalText;
            }
            state.pendingDoneText = finalText;
            state.doneEventReceived = true;
            startTypewriterLoop();
            return;
          }
          finalizeSuccess('');
        })
        .catch(function (error) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          if (state.tokenBuffer && state.tokenBuffer.trim()) {
            state.receivedText = state.tokenBuffer;
            state.pendingDoneText = state.tokenBuffer;
            state.doneEventReceived = true;
            startTypewriterLoop();
            return;
          }
          scheduleResultPoll(error);
        });
    }

    function recoverAfterStreamError(message) {
      if (state.finalized || state.destroyed || !state.isSending) {
        return;
      }
      var taskId = state.currentTaskId;
      if (!taskId) {
        finalizeError(message || '스트림 연결에 실패했습니다.');
        return;
      }

      window.App.apiTransport
        .getTaskStatus(state.sessionId, taskId)
        .then(function (statusResponse) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          var taskStatus = statusResponse && statusResponse.status ? String(statusResponse.status) : '';
          if (taskStatus === 'FAILED') {
            finalizeError(statusResponse.error_message || message || '응답 생성에 실패했습니다.');
            return;
          }
          if (taskStatus === 'COMPLETED') {
            finalizeFromResult();
            return;
          }

          state.streamRetryCount += 1;
          if (state.streamRetryCount > MAX_STREAM_RETRY_COUNT) {
            finalizeError('스트림 재연결 횟수를 초과했습니다.');
            return;
          }
          presenter.setStatus(
            status,
            '스트림 재연결중... (' + state.streamRetryCount + '/' + MAX_STREAM_RETRY_COUNT + ')',
            true,
            'STREAM',
            true
          );
          addTimer(function () {
            connectStream(taskId);
          }, pickStreamRetryDelay(state.streamRetryCount));
        })
        .catch(function (error) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          if (state.tokenBuffer && state.tokenBuffer.trim()) {
            scheduleResultPoll(error);
            return;
          }
          finalizeError(error && error.message ? error.message : message || '스트림 복구에 실패했습니다.');
        });
    }

    function connectStream(taskId) {
      if (state.finalized || state.destroyed || !state.isSending) {
        return;
      }
      detachStream();
      presenter.setStatus(status, '스트림 연결중', true, 'STREAM', true);
      state.streamHandle = window.App.apiTransport.streamTask(state.sessionId, taskId, {
        reconnectGraceMs: 8000,
        onOpen: function () {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          state.streamRetryCount = 0;
          presenter.setStatus(status, '응답 생성중', true, 'STREAM', true);
        },
        onEvent: function (payload) {
          if (state.finalized || state.destroyed || !state.isSending) {
            return;
          }
          var eventType = payload && payload.type ? String(payload.type) : '';
          if (eventType === 'start') {
            presenter.setStatus(status, '응답 생성중', true, 'STREAM', true);
            return;
          }
          if (eventType === 'token') {
            var chunk = payload && typeof payload.content === 'string' ? payload.content : '';
            if (!chunk) {
              return;
            }
            state.tokenBuffer += chunk;
            state.receivedText = state.tokenBuffer;
            state.streamRetryCount = 0;
            startTypewriterLoop();
            presenter.setStatus(status, '응답 수신중', true, 'STREAM', true);
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
            var doneText = '';
            if (
              payload &&
              typeof payload.final_content === 'string' &&
              payload.final_content.trim()
            ) {
              doneText = payload.final_content;
            } else if (
              payload &&
              payload.assistant_message &&
              typeof payload.assistant_message.content === 'string' &&
              payload.assistant_message.content.trim()
            ) {
              doneText = payload.assistant_message.content;
            } else if (state.tokenBuffer && state.tokenBuffer.trim()) {
              doneText = state.tokenBuffer;
            }
            if (doneText) {
              if (!state.tokenBuffer || doneText.indexOf(state.tokenBuffer) === 0) {
                state.tokenBuffer = doneText;
              }
              if (!state.receivedText || doneText.indexOf(state.receivedText) === 0) {
                state.receivedText = doneText;
              }
              state.pendingDoneText = doneText;
              state.doneEventReceived = true;
              startTypewriterLoop();
              return;
            }
            finalizeFromResult();
          }
        },
        onError: function (error) {
          recoverAfterStreamError(error && error.message ? error.message : '스트림 연결에 실패했습니다.');
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
      state.currentTaskId = null;
      state.activeBubble = null;
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
      presenter.setStatus(status, '큐 등록중...', true, 'QUEUE', true);

      var assistantMessage = addAssistantPlaceholder();
      state.activeBubble = assistantMessage.bubble.querySelector('.markdown');
      state.currentTaskId = null;
      state.tokenBuffer = '';
      state.receivedText = '';
      state.visibleText = '';
      state.streamRetryCount = 0;
      state.resultPollCount = 0;
      state.finalized = false;
      state.doneEventReceived = false;
      state.pendingDoneText = '';
      state.streamingTextElement = null;
      state.streamingCaretElement = null;
      renderStreamingBubble();

      window.App.apiTransport
        .queueMessage(state.sessionId, text, DEFAULT_CONTEXT_WINDOW)
        .then(function (response) {
          if (!state.isSending || state.finalized || state.destroyed) {
            return;
          }
          state.currentTaskId = response.task_id;
          presenter.setStatus(status, '큐 등록 완료', true, 'QUEUE', true);
          connectStream(response.task_id);
        })
        .catch(function (error) {
          finalizeError(error && error.message ? error.message : '큐 등록에 실패했습니다.');
        });
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
      state.currentTaskId = null;
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
