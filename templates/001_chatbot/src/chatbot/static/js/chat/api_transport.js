/*
  목적: Chat API 연동 전송 계층 제공
  설명: 세션/메시지/삭제/태스크 API 호출과 SSE 스트림 수신 로직을 캡슐화
  디자인 패턴: 어댑터 패턴
  참조: src/chatbot/api/chat/routers/router.py
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.apiTransport = window.App.apiTransport || {};

  var DEFAULT_CONTEXT_WINDOW = 20;
  var STREAM_CONNECT_DELAY_MS = 1000;

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
    return requestJson('POST', '/ui-api/chat/sessions', body);
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
    var submitPayload = {
      message: String(message || ''),
      context_window: Math.max(1, Number(contextWindow) || DEFAULT_CONTEXT_WINDOW)
    };
    var safeSessionId = String(sessionId || '').trim();
    if (safeSessionId) {
      submitPayload.session_id = safeSessionId;
    }

    var streamController = new AbortController();
    var closed = false;
    var decoder = new TextDecoder();
    var buffer = '';
    var activeSessionId = '';
    var activeRequestId = '';

    function safeClose() {
      if (closed) {
        return;
      }
      closed = true;
      streamController.abort();
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
          var value = line.slice(5);
          if (value.charAt(0) === ' ') {
            value = value.slice(1);
          }
          dataLines.push(value);
        }
      }
      if (!dataLines.length) {
        return null;
      }
      return dataLines.join('\n');
    }

    function validatePayload(payload) {
      if (!payload || typeof payload !== 'object') {
        throw new Error('SSE payload 형식이 올바르지 않습니다.');
      }
      if (typeof payload.type !== 'string' || !payload.type.trim()) {
        throw new Error('SSE payload의 type 필드가 누락되었습니다.');
      }
      if (typeof payload.request_id !== 'string' || !payload.request_id.trim()) {
        throw new Error('SSE payload의 request_id 필드가 누락되었습니다.');
      }
      if (typeof payload.node !== 'string' || !payload.node.trim()) {
        throw new Error('SSE payload의 node 필드가 누락되었습니다.');
      }
      if (payload.request_id !== activeRequestId) {
        throw new Error('요청 ID가 일치하지 않는 이벤트를 수신했습니다.');
      }
      return payload;
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
          parsed = validatePayload(JSON.parse(dataText));
        } catch (error) {
          notifyError(error instanceof Error ? error : new Error('SSE payload 파싱에 실패했습니다.'));
          return;
        }
        if (handlers && typeof handlers.onEvent === 'function') {
          handlers.onEvent(parsed);
        }
        if (parsed.type === 'done' || parsed.type === 'error') {
          safeClose();
          return;
        }
      }
    }

    function waitBeforeStreamConnect() {
      return new Promise(function (resolve) {
        setTimeout(resolve, STREAM_CONNECT_DELAY_MS);
      });
    }

    function openEventStream() {
      var eventPath =
        '/chat/' +
        encodeSegment(activeSessionId) +
        '/events?request_id=' +
        encodeSegment(activeRequestId);
      return fetch(buildPath(eventPath), {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream'
        },
        signal: streamController.signal
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
            handlers.onOpen({
              session_id: activeSessionId,
              request_id: activeRequestId
            });
          }
          if (!response.body || typeof response.body.getReader !== 'function') {
            throw new Error('스트리밍 본문을 읽을 수 없습니다.');
          }
          var reader = response.body.getReader();
          function pump() {
            return reader.read().then(function (result) {
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
        });
    }

    requestJson('POST', '/chat', submitPayload)
      .then(function (queued) {
        if (closed) {
          return;
        }
        activeSessionId = String(queued.session_id || '').trim();
        activeRequestId = String(queued.request_id || '').trim();
        if (!activeSessionId || !activeRequestId) {
          throw new Error('작업 제출 응답이 올바르지 않습니다.');
        }
        if (handlers && typeof handlers.onQueued === 'function') {
          handlers.onQueued({
            session_id: activeSessionId,
            request_id: activeRequestId,
            status: String(queued.status || 'QUEUED')
          });
        }
        return waitBeforeStreamConnect().then(function () {
          if (closed) {
            return;
          }
          return openEventStream();
        });
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
