/*
  목적: 큐/스트림 요청의 모의 동작 제공
  설명: 네트워크 없이 지연을 흉내내는 Promise 기반 모듈
  디자인 패턴: 가짜 어댑터 패턴
  참조: js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.mockTransport = window.App.mockTransport || {};

  var queueCounter = 0;

  window.App.mockTransport.enqueue = function () {
    return new Promise(function (resolve) {
      setTimeout(function () {
        queueCounter += 1;
        resolve({ queueId: 'queue-' + queueCounter });
      }, 250);
    });
  };

  window.App.mockTransport.stream = function () {
    return new Promise(function (resolve) {
      setTimeout(function () {
        resolve([
          '# 미구현 상태입니다',
          '',
          '- 현재는 UI 미리보기용 모의 응답입니다.',
          '- 큐/스트림 라우터 연결 후 실제 응답이 표시됩니다.',
          '',
          '```python',
          'def hello():',
          '    print("미구현 상태입니다")',
          '```',
          ''
        ].join('\n'));
      }, 1200);
    });
  };
})();
