/*
  목적: Chat API 호출용 HTTP 공통 유틸을 제공한다.
  설명: 경로 조립, 에러 메시지 파싱, JSON 요청/응답 처리 로직을 단일 모듈로 관리한다.
  디자인 패턴: 공통 어댑터 유틸
  참조: js/chat/api_transport.js, js/chat/transport/stream.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

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

  window.App.apiTransportHttp = {
    DEFAULT_CONTEXT_WINDOW: DEFAULT_CONTEXT_WINDOW,
    STREAM_CONNECT_DELAY_MS: STREAM_CONNECT_DELAY_MS,
    buildPath: buildPath,
    encodeSegment: encodeSegment,
    parseErrorMessage: parseErrorMessage,
    requestJson: requestJson
  };
})();
