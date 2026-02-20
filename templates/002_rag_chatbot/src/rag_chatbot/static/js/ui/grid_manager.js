/*
  목적: 단일 채팅 셀 + 세션 전환 상태를 관리한다.
  설명: 히스토리 클릭으로 세션을 전환하고, + 버튼 생성/히스토리 삭제를 처리한다.
  디자인 패턴: 컨트롤러 모듈
  참조: js/chat/chat_cell.js, js/chat/api_transport.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.grid = window.App.grid || {};

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

  window.App.grid.init = function () {
    var grid = window.App.utils.qs('#chatGrid');
    var addBtn = window.App.utils.qs('#addCell');
    if (!grid) {
      return;
    }

    window.App.grid.gridEl = grid;
    window.App.grid.cells = [];
    window.App.grid.activeCell = null;
    window.App.grid.activeSessionId = null;
    window.App.grid.sessionMeta = {};
    window.App.grid.isLoading = false;

    if (addBtn) {
      addBtn.addEventListener('click', function () {
        window.App.grid.createNewSession();
      });
    }

    window.App.grid.bootstrapSession();

    window.addEventListener('resize', function () {
      window.App.grid.updateLayout();
    });
  };

  window.App.grid.updateLayout = function () {
    var grid = window.App.grid.gridEl;
    if (!grid) {
      return;
    }
    grid.style.gridTemplateColumns = 'repeat(1, minmax(0, 1fr))';
    grid.style.gridTemplateRows = 'repeat(1, minmax(0, 1fr))';
  };

  window.App.grid.bootstrapSession = function () {
    runLocked(function () {
      return window.App.apiTransport
        .listSessions(50, 0)
        .then(function (response) {
          var sessions = Array.isArray(response.sessions) ? response.sessions : [];
          if (sessions.length === 0) {
            return window.App.grid._createNewSessionInternal();
          }

          sessions.forEach(function (session) {
            registerSessionMeta(
              session.session_id,
              session.title,
              session.last_message_preview || '대기 중'
            );
          });
          return window.App.grid._activateSessionInternal(String(sessions[0].session_id));
        })
        .catch(function (error) {
          console.error('[ui] 세션 목록 조회 실패', error);
          return window.App.grid._createNewSessionInternal();
        });
    });
  };

  window.App.grid.createNewSession = function () {
    runLocked(function () {
      return window.App.grid._createNewSessionInternal();
    });
  };

  window.App.grid.activateSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    runLocked(function () {
      return window.App.grid._activateSessionInternal(String(sessionId));
    });
  };

  window.App.grid.deleteSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    runLocked(function () {
      return window.App.grid._deleteSessionInternal(String(sessionId));
    });
  };

  window.App.grid._createNewSessionInternal = function () {
    return window.App.apiTransport.createSession('새 대화').then(function (response) {
      var sessionId = String(response.session_id);
      registerSessionMeta(sessionId, '새 대화', '대기 중');
      return window.App.grid._activateSessionInternal(sessionId);
    });
  };

  window.App.grid._activateSessionInternal = function (sessionId) {
    if (window.App.grid.activeSessionId === sessionId) {
      if (window.App.app && typeof window.App.app.setActiveHistory === 'function') {
        window.App.app.setActiveHistory(sessionId);
      }
      return Promise.resolve(sessionId);
    }

    var meta = window.App.grid.sessionMeta[sessionId] || { title: '채팅', preview: '대기 중' };
    return loadMessages(sessionId).then(function (messages) {
      var preview = normalizePreview(messages);
      registerSessionMeta(sessionId, meta.title, preview);
      renderActiveCell(sessionId, meta.title, messages);
      window.App.grid.activeSessionId = sessionId;
      if (window.App.app && typeof window.App.app.setActiveHistory === 'function') {
        window.App.app.setActiveHistory(sessionId);
      }
      return sessionId;
    });
  };

  window.App.grid._deleteSessionInternal = function (sessionId) {
    return window.App.apiTransport
      .deleteSession(sessionId)
      .then(function () {
        delete window.App.grid.sessionMeta[sessionId];
        if (window.App.app && typeof window.App.app.removeHistory === 'function') {
          window.App.app.removeHistory(sessionId);
        }
        if (window.App.grid.activeSessionId !== sessionId) {
          return sessionId;
        }
        destroyActiveCell();
        window.App.grid.activeSessionId = null;

        var nextSessionId = pickNextSessionId(sessionId);
        if (nextSessionId) {
          return window.App.grid._activateSessionInternal(nextSessionId);
        }
        return window.App.grid._createNewSessionInternal();
      })
      .catch(function (error) {
        console.error('[ui] 세션 삭제 실패', error);
        window.alert(error && error.message ? error.message : '채팅 삭제에 실패했습니다.');
        return null;
      });
  };
})();
