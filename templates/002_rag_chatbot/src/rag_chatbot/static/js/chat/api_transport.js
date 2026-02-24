/*
  목적: Chat API 연동 전송 계층의 퍼사드 API를 제공한다.
  설명: 세션/메시지 CRUD와 스트림 시작 함수를 하위 transport 모듈에 위임한다.
  디자인 패턴: 퍼사드 패턴
  참조: js/chat/transport/http.js, js/chat/transport/stream.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.apiTransport = window.App.apiTransport || {};

  var http = window.App.apiTransportHttp;
  var stream = window.App.apiTransportStream;

  if (!http || !stream) {
    throw new Error('api_transport 의존 모듈이 로드되지 않았습니다. index.html의 script 순서를 확인하세요.');
  }

  window.App.apiTransport.createSession = function (title) {
    var body = {};
    if (title && String(title).trim()) {
      body.title = String(title).trim();
    }
    return http.requestJson('POST', '/ui-api/chat/sessions', body);
  };

  window.App.apiTransport.listSessions = function (limit, offset) {
    var safeLimit = Math.max(1, Number(limit) || 20);
    var safeOffset = Math.max(0, Number(offset) || 0);
    var path = '/ui-api/chat/sessions?limit=' + safeLimit + '&offset=' + safeOffset;
    return http.requestJson('GET', path);
  };

  window.App.apiTransport.listMessages = function (sessionId, limit, offset) {
    var safeLimit = Math.max(1, Number(limit) || 200);
    var safeOffset = Math.max(0, Number(offset) || 0);
    var path =
      '/ui-api/chat/sessions/' +
      http.encodeSegment(sessionId) +
      '/messages?limit=' +
      safeLimit +
      '&offset=' +
      safeOffset;
    return http.requestJson('GET', path);
  };

  window.App.apiTransport.deleteSession = function (sessionId) {
    var path = '/ui-api/chat/sessions/' + http.encodeSegment(sessionId);
    return http.requestJson('DELETE', path);
  };

  window.App.apiTransport.streamMessage = function (sessionId, message, contextWindow, handlers) {
    return stream.createStreamHandle(sessionId, message, contextWindow, handlers);
  };
})();
