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

  window.App.apiTransport.streamMessage = function (sessionId, message, contextWindow, handlers) {
    var payload = {
      message: String(message || ''),
      context_window: Math.max(1, Number(contextWindow) || DEFAULT_CONTEXT_WINDOW)
    };
    var path = '/chat/sessions/' + encodeSegment(sessionId) + '/messages/stream';
    var controller = new AbortController();
    var closed = false;
    var decoder = new TextDecoder();
    var buffer = '';

    function safeClose() {
      if (closed) {
        return;
      }
      closed = true;
      controller.abort();
      if (handlers && typeof handlers.onClose === 'function') {
        handlers.onClose();
      }
    }

    function notifyError(error) {
      if (handlers && typeof handlers.onError === 'function') {
        handlers.onError(error);
      }
      safeClose();
    }

    function parseSseChunk(raw) {
      var lines = String(raw || '').split('\n');
      var dataLines = [];
      for (var i = 0; i < lines.length; i += 1) {
        var line = lines[i];
        if (!line || line.charAt(0) === ':') {
          continue;
        }
        if (line.indexOf('data:') === 0) {
          dataLines.push(line.slice(5).trimStart());
        }
      }
      if (!dataLines.length) {
        return null;
      }
      return dataLines.join('\n');
    }

    function processBuffer() {
      while (true) {
        var sepIndex = buffer.indexOf('\n\n');
        if (sepIndex < 0) {
          return;
        }
        var block = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        var dataText = parseSseChunk(block);
        if (!dataText) {
          continue;
        }
        var parsed = null;
        try {
          parsed = JSON.parse(dataText);
        } catch (error) {
          notifyError(new Error('SSE payload 파싱에 실패했습니다.'));
          return;
        }
        if (handlers && typeof handlers.onEvent === 'function') {
          handlers.onEvent(parsed);
        }
        if (parsed && (parsed.type === 'done' || parsed.type === 'error')) {
          safeClose();
          return;
        }
      }
    }

    fetch(buildPath(path), {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    })
      .then(function (response) {
        if (!response.ok) {
          return response
            .text()
            .then(function (text) {
              var payload = null;
              if (text) {
                try {
                  payload = JSON.parse(text);
                } catch (ignoreError) {
                  payload = null;
                }
              }
              var message = parseErrorMessage(payload) || ('요청 처리에 실패했습니다. status=' + response.status);
              throw new Error(message);
            });
        }
        if (handlers && typeof handlers.onOpen === 'function') {
          handlers.onOpen();
        }
        if (!response.body || typeof response.body.getReader !== 'function') {
          throw new Error('스트리밍 본문을 읽을 수 없습니다.');
        }
        var reader = response.body.getReader();
        function pump() {
          return reader
            .read()
            .then(function (result) {
              if (closed) {
                return;
              }
              if (result.done) {
                safeClose();
                return;
              }
              buffer += decoder.decode(result.value, { stream: true });
              processBuffer();
              if (closed) {
                return;
              }
              return pump();
            });
        }
        return pump();
      })
      .catch(function (error) {
        if (closed) {
          return;
        }
        notifyError(error instanceof Error ? error : new Error(String(error || '스트림 요청에 실패했습니다.')));
      });

    return {
      close: safeClose
    };
  };
})();
