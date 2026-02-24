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
    helpers.runLocked(function () {
      return window.App.apiTransport
        .listSessions(50, 0)
        .then(function (response) {
          var sessions = Array.isArray(response.sessions) ? response.sessions : [];
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
          return window.App.grid._createNewSessionInternal();
        });
    });
  };

  window.App.grid.createNewSession = function () {
    helpers.runLocked(function () {
      return window.App.grid._createNewSessionInternal();
    });
  };

  window.App.grid.activateSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    helpers.runLocked(function () {
      return window.App.grid._activateSessionInternal(String(sessionId));
    });
  };

  window.App.grid.deleteSession = function (sessionId) {
    if (!sessionId) {
      return;
    }
    helpers.runLocked(function () {
      return window.App.grid._deleteSessionInternal(String(sessionId));
    });
  };

  window.App.grid._createNewSessionInternal = function () {
    return window.App.apiTransport.createSession('새 대화').then(function (response) {
      var sessionId = String(response.session_id);
      helpers.registerSessionMeta(sessionId, '새 대화', '대기 중');
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
    return helpers.loadMessages(sessionId).then(function (messages) {
      var preview = helpers.normalizePreview(messages);
      helpers.registerSessionMeta(sessionId, meta.title, preview);
      helpers.renderActiveCell(sessionId, meta.title, messages);
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
