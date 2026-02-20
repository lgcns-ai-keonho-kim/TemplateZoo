/*
  목적: 개별 채팅 셀 UI 및 API 연동 동작을 처리한다.
  설명: 사용자 입력과 SSE 응답 처리, references 캐러셀/모달 렌더링, 리소스 정리를 구현한다.
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
  var REFERENCE_MODAL_ID = 'referenceModal';
  var ALLOWED_HTML_TAGS = {
    A: true,
    P: true,
    BR: true,
    STRONG: true,
    EM: true,
    CODE: true,
    PRE: true,
    UL: true,
    OL: true,
    LI: true,
    BLOCKQUOTE: true,
    H1: true,
    H2: true,
    H3: true,
    H4: true,
    H5: true,
    H6: true,
    TABLE: true,
    THEAD: true,
    TBODY: true,
    TR: true,
    TH: true,
    TD: true,
    SPAN: true,
    DIV: true
  };

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

  function parseReferences(value) {
    if (!value) {
      return [];
    }
    if (Array.isArray(value)) {
      var normalized = [];
      value.forEach(function (item) {
        var converted = normalizeReference(item);
        if (converted) {
          normalized.push(converted);
        }
      });
      return normalized;
    }
    if (typeof value === 'string') {
      var trimmed = value.trim();
      if (!trimmed) {
        return [];
      }
      try {
        return parseReferences(JSON.parse(trimmed));
      } catch (error) {
        return [];
      }
    }
    return [];
  }

  function normalizeReference(item) {
    if (!item || typeof item !== 'object') {
      return null;
    }

    if (String(item.type || '').toLowerCase() === 'reference') {
      var metadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
      return {
        index: metadata.index !== undefined ? metadata.index : null,
        file_name: String(metadata.file_name || ''),
        file_path: String(metadata.file_path || ''),
        score: metadata.score,
        snippet: metadata.snippet,
        body: typeof item.content === 'string' ? item.content : '',
        metadata: metadata
      };
    }

    var legacyMetadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
    return {
      index: item.index !== undefined ? item.index : legacyMetadata.index,
      file_name: String(item.file_name || legacyMetadata.file_name || ''),
      file_path: String(item.file_path || legacyMetadata.file_path || ''),
      score: item.score !== undefined ? item.score : legacyMetadata.score,
      snippet: item.snippet !== undefined ? item.snippet : legacyMetadata.snippet,
      body: typeof item.body === 'string' ? item.body : (typeof item.content === 'string' ? item.content : ''),
      metadata: legacyMetadata
    };
  }

  function sanitizeLimitedHtml(rawHtml) {
    var template = document.createElement('template');
    template.innerHTML = String(rawHtml || '');

    function sanitizeNode(node) {
      if (!node || !node.childNodes) {
        return;
      }
      var children = Array.prototype.slice.call(node.childNodes);
      children.forEach(function (child) {
        if (child.nodeType === Node.TEXT_NODE) {
          return;
        }
        if (child.nodeType !== Node.ELEMENT_NODE) {
          child.remove();
          return;
        }

        var tagName = String(child.tagName || '').toUpperCase();
        if (!ALLOWED_HTML_TAGS[tagName]) {
          var replacement = document.createTextNode(child.textContent || '');
          child.parentNode.replaceChild(replacement, child);
          return;
        }

        var attributes = Array.prototype.slice.call(child.attributes || []);
        attributes.forEach(function (attribute) {
          var name = String(attribute.name || '').toLowerCase();
          var value = String(attribute.value || '');

          if (name.indexOf('on') === 0) {
            child.removeAttribute(attribute.name);
            return;
          }

          if (tagName === 'A') {
            if (name === 'href') {
              if (value.toLowerCase().indexOf('javascript:') === 0) {
                child.removeAttribute(attribute.name);
                return;
              }
              child.setAttribute('target', '_blank');
              child.setAttribute('rel', 'noopener noreferrer');
              return;
            }
            if (name === 'title' || name === 'target' || name === 'rel') {
              return;
            }
            child.removeAttribute(attribute.name);
            return;
          }

          if (name === 'class') {
            return;
          }
          child.removeAttribute(attribute.name);
        });

        sanitizeNode(child);
      });
    }

    sanitizeNode(template.content);
    return template.innerHTML;
  }

  function ensureReferenceModal() {
    var existing = window.App.utils.qs('#' + REFERENCE_MODAL_ID);
    if (existing) {
      return existing;
    }

    var modal = window.App.utils.createEl('div', 'reference-modal is-hidden');
    modal.id = REFERENCE_MODAL_ID;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');

    var overlay = window.App.utils.createEl('div', 'reference-modal__overlay');
    var panel = window.App.utils.createEl('div', 'reference-modal__panel');
    var header = window.App.utils.createEl('div', 'reference-modal__header');
    var title = window.App.utils.createEl('h3', 'reference-modal__title');
    var closeBtn = window.App.utils.createEl('button', 'reference-modal__close');
    closeBtn.type = 'button';
    closeBtn.textContent = '닫기';

    var meta = window.App.utils.createEl('div', 'reference-modal__meta');
    var bodyWrap = window.App.utils.createEl('div', 'reference-modal__body');

    header.appendChild(title);
    header.appendChild(closeBtn);
    panel.appendChild(header);
    panel.appendChild(meta);
    panel.appendChild(bodyWrap);
    modal.appendChild(overlay);
    modal.appendChild(panel);

    function closeModal() {
      modal.classList.add('is-hidden');
      modal.classList.remove('is-visible');
    }

    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);

    document.body.appendChild(modal);
    return modal;
  }

  function openReferenceModal(reference) {
    var modal = ensureReferenceModal();
    var titleEl = modal.querySelector('.reference-modal__title');
    var metaEl = modal.querySelector('.reference-modal__meta');
    var bodyEl = modal.querySelector('.reference-modal__body');
    if (!titleEl || !metaEl || !bodyEl) {
      return;
    }

    titleEl.textContent = String(reference.file_name || '참고자료');
    metaEl.innerHTML = '';

    function appendMeta(label, value) {
      var text = String(value || '').trim();
      if (!text) {
        return;
      }
      var row = window.App.utils.createEl('div', 'reference-meta-row');
      row.textContent = label + ': ' + text;
      metaEl.appendChild(row);
    }

    appendMeta('파일 경로', reference.file_path);
    appendMeta('점수', reference.score);
    appendMeta('미리보기', reference.snippet);

    if (reference.metadata && typeof reference.metadata === 'object') {
      var metadataRow = window.App.utils.createEl('div', 'reference-meta-row');
      metadataRow.textContent = '메타데이터: ' + JSON.stringify(reference.metadata, null, 2);
      metaEl.appendChild(metadataRow);
    }

    var markdownHtml = window.App.markdown.render(String(reference.body || ''));
    bodyEl.innerHTML = '<div class="markdown">' + sanitizeLimitedHtml(markdownHtml) + '</div>';

    modal.classList.remove('is-hidden');
    modal.classList.add('is-visible');
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
      scrollToBottom(messages, true);
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
      if (!state.activeMessageNode) {
        return;
      }
      var old = state.activeMessageNode.querySelector('.references-carousel');
      if (old) {
        old.remove();
      }
      if (!Array.isArray(references) || references.length === 0) {
        return;
      }

      var wrapper = window.App.utils.createEl('div', 'references-carousel');
      var titleEl = window.App.utils.createEl('div', 'references-carousel__title');
      titleEl.textContent = '참고 자료';
      wrapper.appendChild(titleEl);

      var track = window.App.utils.createEl('div', 'references-carousel__track');
      references.forEach(function (reference) {
        var card = window.App.utils.createEl('button', 'reference-card');
        card.type = 'button';

        var fileName = window.App.utils.createEl('div', 'reference-card__file');
        fileName.textContent = String(reference.file_name || 'unknown');
        card.appendChild(fileName);

        if (reference.file_path) {
          var pathEl = window.App.utils.createEl('div', 'reference-card__path');
          pathEl.textContent = String(reference.file_path);
          card.appendChild(pathEl);
        }

        if (reference.score !== undefined && reference.score !== null) {
          var scoreEl = window.App.utils.createEl('div', 'reference-card__score');
          scoreEl.textContent = 'score: ' + String(reference.score);
          card.appendChild(scoreEl);
        }

        var preview = window.App.utils.createEl('div', 'reference-card__preview');
        preview.textContent = String(reference.body || '').slice(0, 180);
        card.appendChild(preview);

        var detail = window.App.utils.createEl('div', 'reference-card__action');
        detail.textContent = '전문 보기';
        card.appendChild(detail);

        card.addEventListener('click', function () {
          openReferenceModal(reference);
        });
        track.appendChild(card);
      });

      wrapper.appendChild(track);
      state.activeMessageNode.appendChild(wrapper);
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

          if (eventType === 'references') {
            state.references = parseReferences(payload ? payload.content : null);
            presenter.setStatus(status, '참고자료 수신 완료', true, 'STREAM', true);
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

            if (state.references.length === 0 && payload && payload.metadata && payload.metadata.references) {
              state.references = parseReferences(payload.metadata.references);
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
