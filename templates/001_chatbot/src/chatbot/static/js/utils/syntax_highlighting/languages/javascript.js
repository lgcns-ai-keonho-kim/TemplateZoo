/*
  목적: JavaScript 문법 키워드 등록
  설명: 기본 키워드 및 주석 접두어를 등록
  디자인 패턴: 등록 기반 설정
  참조: js/utils/syntax_highlighting/highlight_core.js
*/
(function () {
  'use strict';

  if (!window.App || !window.App.syntax || !window.App.syntax.registerLanguage) {
    return;
  }

  window.App.syntax.registerLanguage(
    'javascript',
    [
      'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while',
      'switch', 'case', 'try', 'catch', 'throw', 'new', 'class', 'extends',
      'import', 'from'
    ],
    '//',
    ['js']
  );
})();
