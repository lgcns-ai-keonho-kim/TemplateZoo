/*
  목적: Chat API 연동 전송 계층 제공
  설명: 세션/메시지/삭제/태스크 API 호출과 SSE 스트림 수신 로직을 캡슐화
  디자인 패턴: 어댑터 패턴
  참조: src/base_template/api/chat/routers/router.py
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.apiTransport = window.App.apiTransport || {};

  var DEFAULT_CONTEXT_WINDOW = 20;

  function buildPath(path) {
    if (!path) {
      return '';
    }
    if (path.charAt(0) === '/') {
      return path;
    }
    return '/' + path;
  }

  function encodeSegment(value) {
    return encodeURIComponent(String(value));
  }

  function parseErrorMessage(payload) {
    if (!payload) {
      return null;
    }
    if (typeof payload === 'string') {
      return payload;
    }
    if (typeof payload.message === 'string' && payload.message.trim()) {
      return payload.message;
    }
    if (payload.detail) {
      if (typeof payload.detail === 'string' && payload.detail.trim()) {
        return payload.detail;
      }
      if (typeof payload.detail.message === 'string' && payload.detail.message.trim()) {
        return payload.detail.message;
      }
    }
    return null;
  }

  function requestJson(method, path, body) {
    var options = {
      method: method,
      headers: {
        'Accept': 'application/json'
      }
    };

    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    return fetch(buildPath(path), options).then(function (response) {
      return response
        .text()
        .then(function (text) {
          var payload = null;
          if (text) {
            try {
              payload = JSON.parse(text);
            } catch (error) {
              payload = null;
            }
          }

          if (!response.ok) {
            var message = parseErrorMessage(payload) || ('요청 처리에 실패했습니다. status=' + response.status);
            var err = new Error(message);
            err.status = response.status;
            err.payload = payload;
            throw err;
          }

          return payload || {};
        });
    });
  }

  window.App.apiTransport.createSession = function (title) {
    var body = {};
    if (title && String(title).trim()) {
      body.title = String(title).trim();
    }
    return requestJson('POST', '/chat/sessions', body);
  };

  window.App.apiTransport.listSessions = function (limit, offset) {
    var safeLimit = Math.max(1, Number(limit) || 20);
    var safeOffset = Math.max(0, Number(offset) || 0);
    var path = '/ui-api/chat/sessions?limit=' + safeLimit + '&offset=' + safeOffset;
    return requestJson('GET', path);
  };

  window.App.apiTransport.listMessages = function (sessionId, limit, offset) {
    var safeLimit = Math.max(1, Number(limit) || 200);
    var safeOffset = Math.max(0, Number(offset) || 0);
    var path =
      '/ui-api/chat/sessions/' +
      encodeSegment(sessionId) +
      '/messages?limit=' +
      safeLimit +
      '&offset=' +
      safeOffset;
    return requestJson('GET', path);
  };

  window.App.apiTransport.deleteSession = function (sessionId) {
    var path = '/ui-api/chat/sessions/' + encodeSegment(sessionId);
    return requestJson('DELETE', path);
  };

  window.App.apiTransport.queueMessage = function (sessionId, message, contextWindow) {
    var payload = {
      message: String(message || ''),
      context_window: Math.max(1, Number(contextWindow) || DEFAULT_CONTEXT_WINDOW)
    };
    var path = '/chat/sessions/' + encodeSegment(sessionId) + '/queue';
    return requestJson('POST', path, payload);
  };

  window.App.apiTransport.getTaskStatus = function (sessionId, taskId) {
    var path =
      '/chat/sessions/' +
      encodeSegment(sessionId) +
      '/tasks/' +
      encodeSegment(taskId) +
      '/status';
    return requestJson('GET', path);
  };

  window.App.apiTransport.getTaskResult = function (sessionId, taskId) {
    var path =
      '/chat/sessions/' +
      encodeSegment(sessionId) +
      '/tasks/' +
      encodeSegment(taskId) +
      '/result';
    return requestJson('GET', path);
  };

  window.App.apiTransport.streamTask = function (sessionId, taskId, handlers) {
    var path =
      '/chat/sessions/' +
      encodeSegment(sessionId) +
      '/tasks/' +
      encodeSegment(taskId) +
      '/stream';
    var source = new EventSource(buildPath(path));
    var closed = false;
    var reconnectGraceMs = Math.max(0, Number(handlers && handlers.reconnectGraceMs) || 8000);
    var errorSince = null;

    function safeClose() {
      if (closed) {
        return;
      }
      closed = true;
      source.close();
      if (handlers && typeof handlers.onClose === 'function') {
        handlers.onClose();
      }
    }

    source.onopen = function () {
      if (closed) {
        return;
      }
      errorSince = null;
      if (handlers && typeof handlers.onOpen === 'function') {
        handlers.onOpen();
      }
    };

    source.onmessage = function (event) {
      if (closed) {
        return;
      }
      errorSince = null;
      var payload = null;
      try {
        payload = JSON.parse(event.data);
      } catch (error) {
        if (handlers && typeof handlers.onError === 'function') {
          handlers.onError(new Error('SSE payload 파싱에 실패했습니다.'));
        }
        safeClose();
        return;
      }

      if (handlers && typeof handlers.onEvent === 'function') {
        handlers.onEvent(payload);
      }

      if (payload && (payload.type === 'done' || payload.type === 'error')) {
        safeClose();
      }
    };

    source.onerror = function () {
      if (closed) {
        return;
      }
      if (errorSince === null) {
        errorSince = Date.now();
      }
      if (handlers && typeof handlers.onTransientError === 'function') {
        handlers.onTransientError();
      }
      var elapsed = Date.now() - errorSince;
      if (elapsed < reconnectGraceMs) {
        return;
      }
      if (handlers && typeof handlers.onError === 'function') {
        handlers.onError(new Error('SSE 연결이 복구되지 않았습니다.'));
      }
      safeClose();
    };

    return {
      close: safeClose
    };
  };
})();
