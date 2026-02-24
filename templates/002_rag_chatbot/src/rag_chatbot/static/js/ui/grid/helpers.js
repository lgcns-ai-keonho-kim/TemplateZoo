/*
  목적: 그리드/세션 관리 보조 함수를 제공한다.
  설명: 세션 메타 갱신, 활성 셀 렌더링, 로딩 잠금 등 공통 절차를 분리한다.
  디자인 패턴: 헬퍼 모듈 패턴
  참조: js/ui/grid_manager.js, js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  function normalizePreview(messages) {
    if (!Array.isArray(messages) || messages.length === 0) {
      return '대기 중';
    }
    var last = messages[messages.length - 1];
    var content = last && typeof last.content === 'string' ? last.content.trim() : '';
    if (!content) {
      return '대기 중';
    }
    return content.split('\n')[0].slice(0, 60);
  }

  function loadMessages(sessionId) {
    return window.App.apiTransport
      .listMessages(sessionId, 200, 0)
      .then(function (response) {
        return Array.isArray(response.messages) ? response.messages : [];
      })
      .catch(function (error) {
        console.error('[ui] 메시지 목록 조회 실패', error);
        return [];
      });
  }

  function setAddButtonState(disabled) {
    var addBtn = window.App.utils.qs('#addCell');
    if (!addBtn) {
      return;
    }
    if (disabled) {
      addBtn.classList.add('btn-disabled');
      addBtn.setAttribute('disabled', 'disabled');
      addBtn.setAttribute('aria-disabled', 'true');
      return;
    }
    addBtn.classList.remove('btn-disabled');
    addBtn.removeAttribute('disabled');
    addBtn.setAttribute('aria-disabled', 'false');
  }

  function runLocked(task) {
    if (window.App.grid.isLoading) {
      return Promise.resolve(null);
    }
    window.App.grid.isLoading = true;
    setAddButtonState(true);
    return Promise.resolve()
      .then(task)
      .finally(function () {
        window.App.grid.isLoading = false;
        setAddButtonState(false);
      });
  }

  function destroyActiveCell() {
    var activeCell = window.App.grid.activeCell;
    if (!activeCell) {
      return;
    }
    if (typeof activeCell.destroy === 'function') {
      activeCell.destroy();
    }
    if (activeCell.element && activeCell.element.parentNode) {
      activeCell.element.parentNode.removeChild(activeCell.element);
    }
    window.App.grid.activeCell = null;
    window.App.grid.cells = [];
  }

  function renderActiveCell(sessionId, title, messages) {
    destroyActiveCell();

    var created = window.App.chatCell.create(sessionId, title, {
      sessionId: sessionId,
      initialMessages: messages
    });
    var cellEl = created && created.element ? created.element : created;
    var destroy = created && typeof created.destroy === 'function'
      ? created.destroy
      : function () {};

    window.App.grid.gridEl.appendChild(cellEl);
    window.App.grid.activeCell = {
      id: sessionId,
      title: title,
      element: cellEl,
      destroy: destroy
    };
    window.App.grid.cells = [window.App.grid.activeCell];
    window.App.grid.updateLayout();
  }

  function registerSessionMeta(sessionId, title, preview) {
    window.App.grid.sessionMeta[sessionId] = {
      title: title && String(title).trim() ? String(title).trim() : '채팅',
      preview: preview && String(preview).trim() ? String(preview).trim() : '대기 중'
    };
    if (window.App.app && window.App.app.onCellCreated) {
      window.App.app.onCellCreated(
        sessionId,
        window.App.grid.sessionMeta[sessionId].title,
        window.App.grid.sessionMeta[sessionId].preview
      );
    }
  }

  function pickNextSessionId(excludedSessionId) {
    var items = window.App.utils.qsa('.history-item');
    var selected = null;
    items.forEach(function (item) {
      if (selected) {
        return;
      }
      var itemSessionId = String(item.getAttribute('data-cell-id') || '');
      if (!itemSessionId || itemSessionId === excludedSessionId) {
        return;
      }
      if (!window.App.grid.sessionMeta[itemSessionId]) {
        return;
      }
      selected = itemSessionId;
    });
    return selected;
  }

  window.App.gridHelpers = {
    normalizePreview: normalizePreview,
    loadMessages: loadMessages,
    runLocked: runLocked,
    destroyActiveCell: destroyActiveCell,
    renderActiveCell: renderActiveCell,
    registerSessionMeta: registerSessionMeta,
    pickNextSessionId: pickNextSessionId
  };
})();
