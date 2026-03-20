/*
  목적: 도구 실행 추적 카드 렌더러를 제공한다.
  설명: tool_start/tool_result/tool_error 이벤트를 assistant 버블 상단 카드로 실시간 렌더링한다.
  디자인 패턴: 상태 캡슐화 뷰 모듈
  참조: js/chat/cell/stream.js, js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  var utils = window.App.utils || {};

  function createEl(tagName, className) {
    if (utils && typeof utils.createEl === 'function') {
      return utils.createEl(tagName, className);
    }
    var el = document.createElement(tagName);
    if (className) {
      el.className = className;
    }
    return el;
  }

  function toText(value) {
    if (value === null || value === undefined) {
      return '';
    }
    return String(value).trim();
  }

  function toInt(value) {
    var num = Number(value);
    if (!Number.isFinite(num)) {
      return null;
    }
    return Math.max(0, Math.round(num));
  }

  function truncate(value, maxLength) {
    var text = toText(value);
    if (text.length <= maxLength) {
      return text;
    }
    return text.slice(0, maxLength - 3) + '...';
  }

  var INTERNAL_TRACE_KEYS = {
    tool_call_id: true,
    retry_for: true,
    attempt: true,
    duration_ms: true,
    ok: true,
    tool_name: true,
    error: true,
    error_code: true
  };

  function parseContentObject(rawContent) {
    if (rawContent && typeof rawContent === 'object' && !Array.isArray(rawContent)) {
      return rawContent;
    }
    var text = toText(rawContent);
    if (!text) {
      return {};
    }
    try {
      var parsed = JSON.parse(text);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed;
      }
      return {};
    } catch (error) {
      return {};
    }
  }

  function stripInternalTrackingFields(value) {
    if (Array.isArray(value)) {
      return value.map(stripInternalTrackingFields);
    }
    if (!value || typeof value !== 'object') {
      return value;
    }

    var sanitized = {};
    Object.keys(value).forEach(function (key) {
      var safeKey = String(key || '').trim();
      if (!safeKey || INTERNAL_TRACE_KEYS[safeKey]) {
        return;
      }
      sanitized[safeKey] = stripInternalTrackingFields(value[key]);
    });
    return sanitized;
  }

  function summarizeOutput(output) {
    if (output === null || output === undefined) {
      return '';
    }
    if (typeof output === 'string') {
      return truncate(output, 180);
    }
    if (typeof output === 'number' || typeof output === 'boolean') {
      return String(output);
    }
    if (Array.isArray(output)) {
      return truncate(JSON.stringify(output), 180);
    }
    if (typeof output === 'object') {
      if (output.value !== undefined && output.value !== null) {
        return truncate(String(output.value), 180);
      }
      return truncate(JSON.stringify(output), 180);
    }
    return truncate(String(output), 180);
  }

  function normalizeToolEvent(eventType, payload, fallbackToolCallId) {
    var safePayload = payload && typeof payload === 'object' ? payload : {};
    var metadata = safePayload.metadata && typeof safePayload.metadata === 'object'
      ? safePayload.metadata
      : {};
    var contentObj = parseContentObject(safePayload.content);

    var toolCallId = toText(
      contentObj.tool_call_id || metadata.tool_call_id || fallbackToolCallId
    );
    var toolName = toText(contentObj.tool_name || metadata.tool_name || 'unknown_tool');
    var outputValue = contentObj.output !== undefined ? contentObj.output : contentObj.result;
    var outputSummary = summarizeOutput(stripInternalTrackingFields(outputValue));
    var errorCode = toText(contentObj.error_code || metadata.error_code);
    var errorMessage = toText(contentObj.error || safePayload.error_message);

    return {
      type: String(eventType || ''),
      toolCallId: toolCallId,
      toolName: toolName,
      outputSummary: outputSummary,
      errorCode: errorCode,
      errorMessage: errorMessage
    };
  }

  function buildDetailLine(model) {
    if (model.type === 'tool_start') {
      return '도구 실행을 시작했습니다.';
    }
    if (model.type === 'tool_result') {
      if (model.outputSummary) {
        return '결과: ' + model.outputSummary;
      }
      return '도구 실행이 완료되었습니다.';
    }
    if (model.type === 'tool_error') {
      var base = model.errorMessage || '도구 실행 중 오류가 발생했습니다.';
      return '오류: ' + base;
    }
    return '';
  }

  function applyCardState(cardNodes, model) {
    cardNodes.root.classList.remove('is-running', 'is-success', 'is-error');
    if (model.type === 'tool_start') {
      cardNodes.root.classList.add('is-running');
      cardNodes.badge.textContent = '실행중';
    } else if (model.type === 'tool_result') {
      cardNodes.root.classList.add('is-success');
      cardNodes.badge.textContent = '성공';
    } else if (model.type === 'tool_error') {
      cardNodes.root.classList.add('is-error');
      cardNodes.badge.textContent = '실패';
    } else {
      cardNodes.badge.textContent = '-';
    }
  }

  function createCard(toolCallId, toolName) {
    var root = createEl('article', 'tool-trace-card');
    root.setAttribute('data-tool-call-id', toolCallId);

    var head = createEl('div', 'tool-trace-head');
    var title = createEl('div', 'tool-trace-title');
    title.textContent = toolName || 'unknown_tool';
    var badge = createEl('span', 'tool-trace-badge');
    badge.textContent = '-';
    head.appendChild(title);
    head.appendChild(badge);

    var detail = createEl('div', 'tool-trace-detail');

    root.appendChild(head);
    root.appendChild(detail);

    return {
      root: root,
      title: title,
      badge: badge,
      detail: detail
    };
  }

  function createController(bubbleEl) {
    if (!bubbleEl || !(bubbleEl instanceof HTMLElement)) {
      throw new Error('tool trace 렌더를 위한 bubble 엘리먼트가 필요합니다.');
    }

    var list = createEl('div', 'tool-trace-list is-hidden');
    var messageEl = bubbleEl.parentElement;
    if (messageEl && messageEl.classList.contains('message')) {
      messageEl.insertBefore(list, bubbleEl);
    } else if (bubbleEl.firstChild) {
      bubbleEl.insertBefore(list, bubbleEl.firstChild);
    } else {
      bubbleEl.appendChild(list);
    }

    var cardsByToolCallId = {};
    var fallbackIndex = 0;

    function ensureCard(model) {
      var key = model.toolCallId || ('tool-call-unknown-' + String(fallbackIndex));
      var existing = cardsByToolCallId[key];
      if (existing) {
        return existing;
      }
      var created = createCard(key, model.toolName);
      cardsByToolCallId[key] = created;
      list.appendChild(created.root);
      list.classList.remove('is-hidden');
      return created;
    }

    function apply(eventType, payload) {
      if (eventType !== 'tool_start' && eventType !== 'tool_result' && eventType !== 'tool_error') {
        return;
      }
      fallbackIndex += 1;
      var model = normalizeToolEvent(
        eventType,
        payload,
        'tool-call-unknown-' + String(fallbackIndex)
      );
      var card = ensureCard(model);

      card.title.textContent = model.toolName || 'unknown_tool';
      card.detail.textContent = buildDetailLine(model);
      applyCardState(card, model);
    }

    function destroy() {
      cardsByToolCallId = {};
      if (list && list.parentNode) {
        list.parentNode.removeChild(list);
      }
    }

    return {
      apply: apply,
      destroy: destroy
    };
  }

  window.App.chatCellToolTrace = {
    create: createController
  };
})();
