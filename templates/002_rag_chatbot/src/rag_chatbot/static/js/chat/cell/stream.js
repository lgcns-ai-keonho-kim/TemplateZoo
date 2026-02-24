/*
  목적: 채팅 셀의 SSE 스트림 연결/이벤트 처리를 제공한다.
  설명: 큐 적재, 토큰 수신, references/done/error 이벤트 분기를 공통 함수로 캡슐화한다.
  디자인 패턴: 전략 주입 기반 오케스트레이션
  참조: js/chat/chat_cell.js, js/chat/api_transport.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  function connect(options) {
    var state = options.state;
    var presenter = options.presenter;
    var status = options.statusEl;
    var userMessage = options.userMessage;
    var contextWindow = Number(options.contextWindow) || 20;
    var detachStream = options.detachStream;
    var setRuntimeInfo = options.setRuntimeInfo;
    var renderStreamingBubble = options.renderStreamingBubble;
    var finalizeSuccess = options.finalizeSuccess;
    var finalizeError = options.finalizeError;
    var parseReferences = options.parseReferences;

    if (state.finalized || state.destroyed || !state.isSending) {
      return;
    }

    detachStream();
    presenter.setStatus(status, '스트림 연결중', true, 'STREAM', true);
    state.streamHandle = window.App.apiTransport.streamMessage(state.sessionId, userMessage, contextWindow, {
      onQueued: function (queued) {
        if (state.finalized || state.destroyed || !state.isSending) {
          return;
        }
        state.activeRequestId = queued && queued.request_id ? String(queued.request_id) : '';
        var queuedSessionId = queued && queued.session_id ? String(queued.session_id) : '';
        if (queuedSessionId) {
          state.sessionId = queuedSessionId;
        }
        presenter.setStatus(status, '작업 큐 적재 완료', true, 'QUEUE', true);
        setRuntimeInfo('queue', null);
      },
      onOpen: function () {
        if (state.finalized || state.destroyed || !state.isSending) {
          return;
        }
        presenter.setStatus(status, '응답 생성중', true, 'STREAM', true);
      },
      onEvent: function (payload) {
        if (state.finalized || state.destroyed || !state.isSending) {
          return;
        }

        var eventType = payload && payload.type ? String(payload.type) : '';
        var eventRequestId = payload && payload.request_id ? String(payload.request_id) : '';
        var eventNode = payload && payload.node ? String(payload.node) : 'unknown';
        var eventMetadata = payload && payload.metadata && typeof payload.metadata === 'object'
          ? payload.metadata
          : null;

        if (state.activeRequestId && eventRequestId && state.activeRequestId !== eventRequestId) {
          return;
        }

        setRuntimeInfo(eventNode, eventMetadata);

        if (eventType === 'start') {
          presenter.setStatus(status, '응답 생성중 [' + eventNode + ']', true, 'STREAM', true);
          return;
        }

        if (eventType === 'token') {
          var chunk = payload && typeof payload.content === 'string' ? payload.content : '';
          if (!chunk) {
            return;
          }
          if (eventNode === 'response') {
            state.tokenBuffer += chunk;
            state.receivedText = state.tokenBuffer;
            renderStreamingBubble();
            presenter.setStatus(status, '응답 수신중 [' + eventNode + ']', true, 'STREAM', true);
            return;
          }
          presenter.setStatus(status, '노드 처리중 [' + eventNode + ']', true, 'STREAM', true);
          return;
        }

        if (eventType === 'references') {
          state.references = parseReferences(payload ? payload.content : null);
          presenter.setStatus(status, '참고자료 수신 완료', true, 'STREAM', true);
          return;
        }

        if (eventType === 'error') {
          finalizeError(payload && payload.error_message ? payload.error_message : null);
          return;
        }

        if (eventType === 'done') {
          var doneStatus = payload && payload.status ? String(payload.status) : '';
          if (doneStatus === 'FAILED') {
            finalizeError(payload && payload.error_message ? payload.error_message : '응답 생성에 실패했습니다.');
            return;
          }

          if (state.references.length === 0 && payload && payload.metadata && payload.metadata.references) {
            state.references = parseReferences(payload.metadata.references);
          }

          var doneContent = payload && typeof payload.content === 'string' ? payload.content : '';
          var doneText = doneContent && doneContent.trim()
            ? doneContent
            : (state.tokenBuffer && state.tokenBuffer.trim() ? state.tokenBuffer : '');

          if (doneText) {
            state.tokenBuffer = doneText;
            state.receivedText = doneText;
            renderStreamingBubble();
            finalizeSuccess(doneText);
            return;
          }

          finalizeSuccess(state.tokenBuffer || '');
        }
      },
      onError: function (error) {
        if (state.finalized || state.destroyed || !state.isSending) {
          return;
        }
        if (state.tokenBuffer && state.tokenBuffer.trim()) {
          finalizeSuccess(state.tokenBuffer);
          return;
        }
        finalizeError(error && error.message ? error.message : '스트림 연결에 실패했습니다.');
      }
    });
  }

  window.App.chatCellStream = {
    connect: connect
  };
})();
