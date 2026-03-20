/*
  목적: 1회성 Agent 화면 초기화와 요청 실행을 담당한다.
  설명: `/agent` 단건 호출, 상태 표시, 최종 응답 렌더링을 수행한다.
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

  function setRunId(node, value) {
    node.textContent = value || '아직 생성되지 않음';
  }

  function resolveStatusLabel(status) {
    var normalized = String(status || '').trim().toUpperCase();
    if (normalized === 'COMPLETED') {
      return { label: '완료', className: 'is-completed' };
    }
    if (normalized === 'RUNNING') {
      return { label: '실행 중', className: 'is-running' };
    }
    if (normalized === 'BLOCKED') {
      return { label: '차단됨', className: 'is-blocked' };
    }
    if (normalized === 'FAILED' || normalized === 'ERROR') {
      return { label: '오류', className: 'is-error' };
    }
    return { label: '대기', className: '' };
  }

  function renderOutput(container, text) {
    container.innerHTML = '<div class="markdown">' + window.App.markdown.render(text || '') + '</div>';
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
    var runIdValue = window.App.utils.qs('#runIdValue');

    if (!form || !input || !button || !resultOutput || !statusChip || !runIdValue) {
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
      setRunId(runIdValue, '할당 대기');
      resultOutput.innerHTML =
        '<div class="result-placeholder">요청을 서버에 전달했습니다. 실행이 끝나면 최종 산출물이 이 영역에 반영됩니다.</div>';

      try {
        var payload = await executeRequest({ request: request });
        var statusMeta = resolveStatusLabel(payload.status);
        renderOutput(resultOutput, String(payload.output_text || ''));
        setStatus(statusChip, statusMeta.label, statusMeta.className);
        setRunId(runIdValue, String(payload.run_id || '미반환'));
      } catch (error) {
        setStatus(statusChip, '오류', 'is-error');
        setRunId(runIdValue, '생성 실패');
        resultOutput.innerHTML =
          '<div class="result-placeholder">' +
          window.App.utils.escapeHtml(error && error.message ? error.message : '요청 처리에 실패했습니다.') +
          '</div>';
      } finally {
        button.disabled = false;
      }
    });
  };

  document.addEventListener('DOMContentLoaded', function () {
    window.App.agentApp.init();
  });
})();
