/*
  목적: 1회성 Agent 화면 초기화와 요청 실행을 담당한다.
  설명: `/agent` 단건 호출, 상태 표시, 결과/Tool 카드 렌더링을 수행한다.
  디자인 패턴: 모듈 패턴
  참조: js/utils/dom.js, js/utils/markdown.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.agentApp = window.App.agentApp || {};

  function parseErrorMessage(payload, status) {
    if (payload && typeof payload.message === 'string' && payload.message.trim()) {
      return payload.message.trim();
    }
    if (payload && payload.detail && typeof payload.detail === 'object') {
      if (typeof payload.detail.message === 'string' && payload.detail.message.trim()) {
        return payload.detail.message.trim();
      }
      if (typeof payload.detail.error === 'string' && payload.detail.error.trim()) {
        return payload.detail.error.trim();
      }
    }
    return '요청 처리에 실패했습니다. status=' + status;
  }

  function setStatus(chip, label, className) {
    chip.textContent = label;
    chip.className = 'status-chip';
    if (className) {
      chip.classList.add(className);
    }
  }

  function renderOutput(container, text) {
    container.innerHTML = '<div class="markdown">' + window.App.markdown.render(text || '') + '</div>';
  }

  function renderToolCards(container, toolResults) {
    container.innerHTML = '';
    if (!Array.isArray(toolResults) || toolResults.length === 0) {
      return;
    }

    toolResults.forEach(function (item) {
      var card = window.App.utils.createEl('section', 'tool-card');
      var header = window.App.utils.createEl('div', 'tool-card__header');
      var name = window.App.utils.createEl('div', 'tool-card__name');
      var status = window.App.utils.createEl('div', 'tool-card__status');
      var body = window.App.utils.createEl('pre');

      name.textContent = String(item.tool_name || 'unknown');
      status.textContent = String(item.status || 'UNKNOWN');
      status.classList.add(item.status === 'SUCCESS' ? 'is-success' : 'is-failed');

      if (item.status === 'SUCCESS') {
        body.textContent = JSON.stringify(item.output || {}, null, 2);
      } else {
        body.textContent = String(item.error_message || 'Tool 실행 실패');
      }

      header.appendChild(name);
      header.appendChild(status);
      card.appendChild(header);
      card.appendChild(body);
      container.appendChild(card);
    });
  }

  async function executeRequest(options) {
    var response = await fetch('/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ request: options.request })
    });

    var payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }

    if (!response.ok) {
      throw new Error(parseErrorMessage(payload, response.status));
    }
    return payload;
  }

  window.App.agentApp.init = function () {
    window.App.theme.init();

    var form = window.App.utils.qs('#requestForm');
    var input = window.App.utils.qs('#requestInput');
    var button = window.App.utils.qs('#runButton');
    var resultOutput = window.App.utils.qs('#resultOutput');
    var statusChip = window.App.utils.qs('#statusChip');
    var toolResults = window.App.utils.qs('#toolResults');

    if (!form || !input || !button || !resultOutput || !statusChip || !toolResults) {
      return;
    }

    form.addEventListener('submit', async function (event) {
      event.preventDefault();

      var request = String(input.value || '').trim();
      if (!request) {
        setStatus(statusChip, '요청을 입력하세요', 'is-error');
        return;
      }

      button.disabled = true;
      setStatus(statusChip, '실행 중', 'is-running');
      resultOutput.innerHTML = '<div class="result-placeholder">Agent가 요청을 처리하고 있습니다.</div>';
      toolResults.innerHTML = '';

      try {
        var payload = await executeRequest({ request: request });
        renderOutput(resultOutput, String(payload.output_text || ''));
        renderToolCards(toolResults, payload.tool_results);
        if (payload.status === 'BLOCKED') {
          setStatus(statusChip, '차단됨', 'is-blocked');
        } else {
          setStatus(statusChip, '완료', 'is-completed');
        }
      } catch (error) {
        setStatus(statusChip, '오류', 'is-error');
        resultOutput.innerHTML =
          '<div class="result-placeholder">' +
          window.App.utils.escapeHtml(error && error.message ? error.message : '요청 처리에 실패했습니다.') +
          '</div>';
        toolResults.innerHTML = '';
      } finally {
        button.disabled = false;
      }
    });
  };

  document.addEventListener('DOMContentLoaded', function () {
    window.App.agentApp.init();
  });
})();
