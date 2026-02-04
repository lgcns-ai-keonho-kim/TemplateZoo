/*
  목적: 개별 채팅 셀 UI 및 상호작용 처리
  설명: 메시지 전송, 타입라이터 효과, 중지 버튼, 상태 표시 구현
  디자인 패턴: 상태 캡슐화 컴포넌트
  참조: js/chat/mock_transport.js, js/utils/markdown.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.chatCell = window.App.chatCell || {};

  var escapeHtml = window.App.utils.escapeHtml;
  var STAGE_LABELS = {
    QUEUE: '큐',
    STREAM: '스트림',
    DONE: '완료',
    STOP: '중지'
  };

  function createMessage(role, contentHtml) {
    var message = window.App.utils.createEl('div', 'message ' + role);
    var bubble = window.App.utils.createEl('div', 'message__bubble');
    bubble.innerHTML = contentHtml;
    message.appendChild(bubble);

    var meta = window.App.utils.createEl('div', 'message__meta');
    meta.textContent = window.App.utils.formatTime();
    message.appendChild(meta);

    return { message: message, bubble: bubble };
  }

  function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
  }

  function setStatus(statusEl, text, showSpinner, stage, isActive) {
    var label = statusEl.querySelector('.status-text');
    var pill = statusEl.querySelector('.status-pill');
    var spinner = statusEl.querySelector('.spinner');

    if (stage) {
      statusEl.setAttribute('data-stage', stage);
    }

    if (pill) {
      var stageKey = statusEl.getAttribute('data-stage') || 'QUEUE';
      pill.textContent = STAGE_LABELS[stageKey] || stageKey;
    }

    label.textContent = text;

    if (showSpinner) {
      spinner.classList.remove('is-hidden');
    } else {
      spinner.classList.add('is-hidden');
    }

    if (isActive) {
      statusEl.classList.add('is-active');
    } else {
      statusEl.classList.remove('is-active');
    }
  }

  function setSendingState(state, sending, sendBtn, stopBtn, inputEl) {
    state.isSending = sending;
    if (sending) {
      sendBtn.classList.add('btn-disabled');
      stopBtn.classList.remove('btn-disabled');
      stopBtn.classList.remove('is-hidden');
      inputEl.setAttribute('disabled', 'disabled');
    } else {
      sendBtn.classList.remove('btn-disabled');
      stopBtn.classList.add('btn-disabled');
      stopBtn.classList.add('is-hidden');
      inputEl.removeAttribute('disabled');
    }
  }

  function startTypewriter(state, targetEl, fullText, onComplete) {
    var index = 0;
    var caret = '<span class="typing-caret"></span>';

    state.typewriterTimer = setInterval(function () {
      if (!state.isSending) {
        clearInterval(state.typewriterTimer);
        return;
      }
      index += 1;
      var partial = fullText.slice(0, index);
      targetEl.innerHTML = window.App.markdown.render(partial, { allowHtml: true }) + caret;
      if (index >= fullText.length) {
        clearInterval(state.typewriterTimer);
        state.typewriterTimer = null;
        onComplete();
      }
    }, 22);
  }

  window.App.chatCell.create = function (cellId, title) {
    var state = {
      id: cellId,
      title: title,
      isSending: false,
      typewriterTimer: null,
      activeBubble: null,
      timers: []
    };

    var cell = window.App.utils.createEl('section', 'chat-cell');
    cell.setAttribute('data-cell-id', cellId);

    var header = window.App.utils.createEl('div', 'chat-cell__header');
    var headerTitle = window.App.utils.createEl('div', 'chat-cell__title');
    headerTitle.textContent = title;
    var headerActions = window.App.utils.createEl('div', 'chat-cell__actions');

    var expandBtn = window.App.utils.createEl('button', 'btn-ghost btn-expand');
    expandBtn.type = 'button';
    expandBtn.setAttribute('title', '최대화');
    expandBtn.setAttribute('aria-label', '최대화');
    var expandIcon = window.App.utils.createEl('img', 'icon');
    expandIcon.setAttribute('src', 'asset/icons/maximize.svg');
    expandIcon.setAttribute('alt', '');
    expandBtn.appendChild(expandIcon);

    var restoreBtn = window.App.utils.createEl('button', 'btn-ghost btn-restore');
    restoreBtn.type = 'button';
    restoreBtn.setAttribute('title', '돌아가기');
    restoreBtn.setAttribute('aria-label', '돌아가기');
    var restoreIcon = window.App.utils.createEl('img', 'icon');
    restoreIcon.setAttribute('src', 'asset/icons/minimize.svg');
    restoreIcon.setAttribute('alt', '');
    restoreBtn.appendChild(restoreIcon);

    var closeBtn = window.App.utils.createEl('button', 'btn-ghost btn-close is-hidden');
    closeBtn.type = 'button';
    closeBtn.setAttribute('title', '닫기');
    closeBtn.setAttribute('aria-label', '닫기');
    var closeIcon = window.App.utils.createEl('img', 'icon');
    closeIcon.setAttribute('src', 'asset/icons/close.svg');
    closeIcon.setAttribute('alt', '');
    closeBtn.appendChild(closeIcon);

    headerActions.appendChild(expandBtn);
    headerActions.appendChild(restoreBtn);
    headerActions.appendChild(closeBtn);
    header.appendChild(headerTitle);
    header.appendChild(headerActions);

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

    function updateHistory(preview) {
      if (window.App.app && window.App.app.updateHistory) {
        window.App.app.updateHistory(cellId, headerTitle.textContent, preview);
      }
    }

    function addUserMessage(text) {
      var html = '<div class="markdown">' + window.App.markdown.render(text, { allowHtml: true }) + '</div>';
      var created = createMessage('user', html);
      messages.appendChild(created.message);
      scrollToBottom(messages);
      updateHistory(text);
    }

    function addAssistantPlaceholder() {
      var bubbleContent = '<div class="markdown"></div>';
      var created = createMessage('assistant', bubbleContent);
      messages.appendChild(created.message);
      scrollToBottom(messages);
      return created;
    }

    function clearTimers() {
      state.timers.forEach(function (timerId) {
        clearTimeout(timerId);
      });
      state.timers = [];
      if (state.typewriterTimer) {
        clearInterval(state.typewriterTimer);
        state.typewriterTimer = null;
      }
    }

    function handleStop() {
      if (!state.isSending) {
        return;
      }
      clearTimers();
      if (state.activeBubble) {
        var caret = state.activeBubble.querySelector('.typing-caret');
        if (caret) {
          caret.remove();
        }
      }
      setSendingState(state, false, sendBtn, stopBtn, input);
      status.classList.add('is-visible');
      setStatus(status, '중지됨', false, 'STOP', false);
      var hideTimer = setTimeout(function () {
        status.classList.remove('is-visible');
      }, 1200);
      state.timers.push(hideTimer);
      state.activeBubble = null;
    }

    function handleSend() {
      var text = input.value.trim();
      if (!text || state.isSending) {
        return;
      }

      input.value = '';
      adjustTextareaHeight();
      addUserMessage(text);
      setSendingState(state, true, sendBtn, stopBtn, input);
      status.classList.add('is-visible');
      setStatus(status, '생각중...', true, 'QUEUE', true);

      var assistantMessage = addAssistantPlaceholder();
      var messageBubble = assistantMessage.bubble.querySelector('.markdown');
      state.activeBubble = messageBubble;

      window.App.mockTransport.enqueue().then(function (queueRes) {
        if (!state.isSending) {
          return;
        }
        setStatus(status, '큐 완료, 스트림 대기중', true, 'QUEUE', true);

        var waitTimer = setTimeout(function () {
          if (!state.isSending) {
            return;
          }
          setStatus(status, '스트림 연결중', true, 'STREAM', true);

          window.App.mockTransport.stream(queueRes.queueId).then(function (responseText) {
            if (!state.isSending) {
              return;
            }
            setStatus(status, '응답 수신중', true, 'STREAM', true);
            startTypewriter(state, messageBubble, responseText, function () {
              if (!state.isSending) {
                return;
              }
              messageBubble.innerHTML = window.App.markdown.render(responseText, { allowHtml: true });
              updateHistory(responseText.split('\n')[0]);
              setStatus(status, '완료', false, 'DONE', false);
              setSendingState(state, false, sendBtn, stopBtn, input);
              state.activeBubble = null;
              scrollToBottom(messages);
              var doneTimer = setTimeout(function () {
                status.classList.remove('is-visible');
              }, 1000);
              state.timers.push(doneTimer);
            });
          });
        }, 1000);

        state.timers.push(waitTimer);
      });
    }

    sendBtn.addEventListener('click', handleSend);
    stopBtn.addEventListener('click', handleStop);
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    });

    function setCellActive() {
      var activeCells = document.querySelectorAll('.chat-cell.is-active');
      activeCells.forEach(function (activeCell) {
        if (activeCell !== cell) {
          activeCell.classList.remove('is-active');
        }
      });
      cell.classList.add('is-active');
    }

    function adjustTextareaHeight() {
      var maxHeight = 220;
      input.style.height = 'auto';
      var nextHeight = Math.min(input.scrollHeight, maxHeight);
      input.style.height = nextHeight + 'px';
    }

    input.addEventListener('focus', setCellActive);
    input.addEventListener('blur', function () {
      cell.classList.remove('is-active');
    });
    input.addEventListener('input', adjustTextareaHeight);

    expandBtn.addEventListener('click', function () {
      window.App.grid.setExpanded(cellId);
    });

    restoreBtn.addEventListener('click', function () {
      window.App.grid.clearExpanded();
    });

    closeBtn.addEventListener('click', function () {
      window.App.grid.removeCell(cellId);
    });

    return cell;
  };
})();
