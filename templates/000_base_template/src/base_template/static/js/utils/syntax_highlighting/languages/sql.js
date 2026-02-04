/*
  목적: SQL 문법 키워드 등록
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
    'sql',
    [
      'select', 'from', 'where', 'join', 'left', 'right', 'inner', 'outer', 'on',
      'insert', 'into', 'values', 'update', 'set', 'delete', 'create', 'table',
      'alter', 'drop', 'limit', 'group', 'by', 'order', 'asc', 'desc'
    ],
    '--'
  );
})();
