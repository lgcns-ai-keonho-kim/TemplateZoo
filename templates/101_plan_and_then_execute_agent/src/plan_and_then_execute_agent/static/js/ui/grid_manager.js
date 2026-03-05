/*
  목적: 단일 채팅 셀 + 세션 전환 상태를 관리한다.
  설명: 히스토리 클릭 전환, 새 세션 생성, 세션 삭제/대체 활성화를 조정한다.
  디자인 패턴: 컨트롤러 모듈 + 헬퍼 위임
  참조: js/ui/grid/helpers.js, js/chat/chat_cell.js, js/chat/api_transport.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.grid = window.App.grid || {};

  var helpers = window.App.gridHelpers;
  if (!helpers) {
    throw new Error('grid_manager 의존 모듈이 로드되지 않았습니다. index.html의 script 순서를 확인하세요.');
  }

  function normalizeSessionId(value) {
    return String(value || '').trim();
  }

  function normalizeSessionTitle(value) {
    var title = String(value || '').trim();
    if (!title) {
      return '새 대화';
    }
    return title;
  }

  function normalizeUiErrorMessage(error, fallbackMessage) {
    var presenter = window.App.chatPresenter;
    var rawMessage = error && error.message ? String(error.message) : '';
    if (presenter && typeof presenter.normalizeErrorMessage === 'function') {
      return presenter.normalizeErrorMessage(rawMessage, fallbackMessage);
    }
    return rawMessage || String(fallbackMessage || '요청 처리에 실패했습니다.');
  }

  function showUiError(error, fallbackMessage) {
    var message = normalizeUiErrorMessage(error, fallbackMessage);
    window.alert(message);
  }

  function normalizeSessionsResponse(response) {
    var source = response && Array.isArray(response.sessions) ? response.sessions : [];
    var normalized = [];
    source.forEach(function (session) {
      if (!session || typeof session !== 'object') {
        return;
      }
      var sessionId = normalizeSessionId(session.session_id);
      if (!sessionId) {
        return;
      }
      normalized.push({
        session_id: sessionId,
        title: normalizeSessionTitle(session.title),
        last_message_preview: session.last_message_preview
      });
    });
    return normalized;
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
    return helpers.runLocked(function () {
      return window.App.apiTransport
        .listSessions(50, 0)
        .then(function (response) {
          var sessions = normalizeSessionsResponse(response);
          if (sessions.length === 0) {
            return window.App.grid._createNewSessionInternal();
          }

          sessions.forEach(function (session) {
            helpers.registerSessionMeta(
              session.session_id,
              session.title,
              session.last_message_preview || '대기 중'
            );
          });
          return window.App.grid._activateSessionInternal(String(sessions[0].session_id));
        })
        .catch(function (error) {
          console.error('[ui] 세션 목록 조회 실패', error);
          return window.App.grid._createNewSessionInternal().catch(function (createError) {
            console.error('[ui] 초기 세션 생성 실패', createError);
            showUiError(createError, '초기 세션 생성에 실패했습니다.');
            return null;
          });
        });
    });
  };

  window.App.grid.createNewSession = function () {
    return helpers.runLocked(function () {
      return window.App.grid._createNewSessionInternal();
    }).catch(function (error) {
      console.error('[ui] 새 세션 생성 실패', error);
      showUiError(error, '새 세션 생성에 실패했습니다.');
      return null;
    });
  };

  window.App.grid.activateSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    return helpers.runLocked(function () {
      return window.App.grid._activateSessionInternal(String(sessionId));
    }).catch(function (error) {
      console.error('[ui] 세션 전환 실패', error);
      showUiError(error, '세션 전환에 실패했습니다.');
      return null;
    });
  };

  window.App.grid.deleteSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    return helpers.runLocked(function () {
      return window.App.grid._deleteSessionInternal(String(sessionId));
    });
  };

  window.App.grid._createNewSessionInternal = function () {
    return window.App.apiTransport.createSession('새 대화').then(function (response) {
      var sessionId = normalizeSessionId(response && response.session_id);
      if (!sessionId) {
        throw new Error('세션 생성 응답에 session_id가 없습니다.');
      }
      var title = '새 대화';
      helpers.registerSessionMeta(sessionId, title, '대기 중');
      return window.App.grid._activateSessionInternal(sessionId);
    });
  };

  window.App.grid._activateSessionInternal = function (sessionId) {
    var safeSessionId = normalizeSessionId(sessionId);
    if (!safeSessionId) {
      return Promise.reject(new Error('유효하지 않은 세션 ID입니다.'));
    }
    if (window.App.grid.activeSessionId === safeSessionId) {
      if (window.App.app && typeof window.App.app.setActiveHistory === 'function') {
        window.App.app.setActiveHistory(safeSessionId);
      }
      return Promise.resolve(safeSessionId);
    }

    var meta = window.App.grid.sessionMeta[safeSessionId] || { title: '채팅', preview: '대기 중' };
    return helpers.loadMessages(safeSessionId).then(function (messages) {
      var preview = helpers.normalizePreview(messages);
      helpers.registerSessionMeta(safeSessionId, meta.title, preview);
      helpers.renderActiveCell(safeSessionId, meta.title, messages);
      window.App.grid.activeSessionId = safeSessionId;
      if (window.App.app && typeof window.App.app.setActiveHistory === 'function') {
        window.App.app.setActiveHistory(safeSessionId);
      }
      return safeSessionId;
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
        helpers.destroyActiveCell();
        window.App.grid.activeSessionId = null;

        var nextSessionId = helpers.pickNextSessionId(sessionId);
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
