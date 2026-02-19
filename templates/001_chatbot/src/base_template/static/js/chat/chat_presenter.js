/*
  목적: Chat 셀 UI 렌더링 보조 로직을 제공한다.
  설명: 메시지/상태 렌더링과 입력 전송 상태 토글을 공통 함수로 분리한다.
  디자인 패턴: 프레젠터 패턴
  참조: js/chat/chat_cell.js, js/utils/markdown.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.chatPresenter = window.App.chatPresenter || {};

  var STAGE_LABELS = {
    QUEUE: '큐',
    STREAM: '스트림',
    DONE: '완료',
    STOP: '중지',
    FAIL: '실패'
  };

  window.App.chatPresenter.firstLine = function (text) {
    var raw = String(text || '').trim();
    if (!raw) {
      return '';
    }
    return raw.split('\n')[0];
  };

  window.App.chatPresenter.normalizeRole = function (value) {
    var role = String(value || '').toLowerCase();
    if (role === 'assistant') {
      return 'assistant';
    }
    return 'user';
  };

  window.App.chatPresenter.createMessageNode = function (role, contentHtml) {
    var message = window.App.utils.createEl('div', 'message ' + role);
    var bubble = window.App.utils.createEl('div', 'message__bubble');
    bubble.innerHTML = contentHtml;
    message.appendChild(bubble);

    var meta = window.App.utils.createEl('div', 'message__meta');
    meta.textContent = window.App.utils.formatTime();
    message.appendChild(meta);

    return { message: message, bubble: bubble };
  };

  window.App.chatPresenter.renderMessageHtml = function (text) {
    var safeMarkdown = window.App.markdown.render(String(text || ''));
    return '<div class="markdown">' + safeMarkdown + '</div>';
  };

  window.App.chatPresenter.renderStreamingHtml = function (text, withCaret) {
    var safeMarkdown = window.App.markdown.render(String(text || ''));
    if (withCaret) {
      return safeMarkdown + '<span class="typing-caret"></span>';
    }
    return safeMarkdown;
  };

  window.App.chatPresenter.renderRealtimeStreamingHtml = function (text, withCaret) {
    var safeMarkdown = window.App.markdown.render(String(text || ''));
    if (withCaret) {
      return safeMarkdown + '<span class="typing-caret"></span>';
    }
    return safeMarkdown;
  };

  window.App.chatPresenter.setStatus = function (statusEl, text, showSpinner, stage, isActive) {
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

    if (label) {
      label.textContent = text;
    }

    if (spinner) {
      if (showSpinner) {
        spinner.classList.remove('is-hidden');
      } else {
        spinner.classList.add('is-hidden');
      }
    }

    if (isActive) {
      statusEl.classList.add('is-active');
    } else {
      statusEl.classList.remove('is-active');
    }
  };

  function summarizeMetadata(metadata) {
    if (!metadata || typeof metadata !== 'object') {
      return '';
    }
    var usage = metadata.token_usage || metadata.usage || null;
    var docs = metadata.references || metadata.documents || null;
    var parts = [];
    if (usage && typeof usage === 'object') {
      var totalTokens = Number(usage.total_tokens || usage.total || usage.output_tokens || 0);
      if (totalTokens > 0) {
        parts.push('tokens=' + String(totalTokens));
      }
    }
    if (Array.isArray(docs) && docs.length > 0) {
      parts.push('refs=' + String(docs.length));
    }
    if (parts.length === 0) {
      return '';
    }
    return parts.join(', ');
  }

  window.App.chatPresenter.setRuntimeInfo = function (statusEl, node, metadata) {
    var runtimeEl = statusEl.querySelector('.status-runtime');
    if (!runtimeEl) {
      runtimeEl = window.App.utils.createEl('span', 'status-runtime');
      statusEl.appendChild(runtimeEl);
    }
    var safeNode = typeof node === 'string' && node.trim() ? node.trim() : '';
    var metaSummary = summarizeMetadata(metadata);
    if (!safeNode && !metaSummary) {
      runtimeEl.textContent = '';
      runtimeEl.classList.add('is-hidden');
      return;
    }
    runtimeEl.classList.remove('is-hidden');
    if (safeNode && metaSummary) {
      runtimeEl.textContent = '[' + safeNode + '] ' + metaSummary;
      return;
    }
    runtimeEl.textContent = safeNode ? ('[' + safeNode + ']') : metaSummary;
  };

  window.App.chatPresenter.setSendingState = function (state, sending, sendBtn, stopBtn, inputEl) {
    state.isSending = sending;
    if (sending) {
      sendBtn.classList.add('btn-disabled');
      stopBtn.classList.remove('btn-disabled');
      stopBtn.classList.remove('is-hidden');
      inputEl.setAttribute('disabled', 'disabled');
      return;
    }
    sendBtn.classList.remove('btn-disabled');
    stopBtn.classList.add('btn-disabled');
    stopBtn.classList.add('is-hidden');
    inputEl.removeAttribute('disabled');
  };
})();
