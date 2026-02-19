/*
  목적: HTML 문법 키워드 등록
  설명: 기본 태그 및 속성 키워드를 등록
  디자인 패턴: 등록 기반 설정
  참조: js/utils/syntax_highlighting/highlight_core.js
*/
(function () {
  'use strict';

  if (!window.App || !window.App.syntax || !window.App.syntax.registerLanguage) {
    return;
  }

  window.App.syntax.registerLanguage(
    'html',
    [
      'div', 'span', 'section', 'header', 'main', 'aside', 'footer', 'script',
      'style', 'class', 'id', 'href', 'src'
    ],
    '<!--'
  );
})();
