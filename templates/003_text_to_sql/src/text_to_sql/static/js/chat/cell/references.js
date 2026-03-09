/*
  목적: 참고자료(reference) 통합 퍼사드를 제공한다.
  설명: 파서 모듈과 뷰 모듈을 결합해 채팅 셀에서 단일 API로 사용하게 한다.
  디자인 패턴: 퍼사드 패턴
  참조: js/chat/cell/reference_parser.js, js/chat/cell/reference_view.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  var parser = window.App.chatCellReferenceParser;
  var view = window.App.chatCellReferenceView;

  if (!parser || !view) {
    throw new Error('references 의존 모듈이 로드되지 않았습니다. index.html의 script 순서를 확인하세요.');
  }

  window.App.chatCellReferences = {
    parse: parser.parse,
    renderCarousel: view.renderCarousel
  };
})();
