/*
  목적: 문법 강조 모듈의 진입점 제공
  설명: 레지스트리 상태를 확인하고 기본 초기화만 수행
  디자인 패턴: 초기화 엔트리 포인트
  참조: js/utils/syntax_highlighting/highlight_core.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.syntax = window.App.syntax || {};
  window.App.syntax.isReady = true;
})();
