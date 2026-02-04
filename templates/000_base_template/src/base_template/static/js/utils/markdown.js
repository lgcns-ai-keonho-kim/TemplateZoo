/*
  목적: 간단한 마크다운 렌더링 제공
  설명: 제목, 리스트, 인라인 강조, 코드 블록 등 핵심 기능만 지원 (신뢰된 HTML 허용 가능)
  디자인 패턴: 함수형 유틸 모듈
  참조: js/utils/syntax_highlighting/highlight_core.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.markdown = window.App.markdown || {};

  var escapeHtml = window.App.utils.escapeHtml;

  /** @param {string} text */
  function renderInline(text, options) {
    var raw = String(text);
    var allowHtml = options && options.allowHtml === true;
    var escaped = allowHtml ? raw : escapeHtml(raw);
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    return escaped;
  }

  /** @param {string[]} listItems */
  function renderList(listItems, options) {
    var itemsHtml = listItems
      .map(function (item) {
        return '<li>' + renderInline(item, options) + '</li>';
      })
      .join('');
    return '<ul>' + itemsHtml + '</ul>';
  }

  /** @param {string} code */
  function renderCodeBlock(code, language) {
    var highlighted = window.App.syntax.highlight(code, language);
    var langClass = language ? ' language-' + escapeHtml(language) : '';
    return '<pre><code class="' + langClass + '">' + highlighted + '</code></pre>';
  }

  /** @param {string} text */
  window.App.markdown.render = function (text, options) {
    var lines = String(text).replace(/\r\n/g, '\n').split('\n');
    var html = '';
    var inCode = false;
    var codeLang = '';
    var codeBuffer = [];
    var listBuffer = [];

    function flushList() {
      if (listBuffer.length > 0) {
        html += renderList(listBuffer, options);
        listBuffer = [];
      }
    }

    lines.forEach(function (line) {
      var trimmed = line.trim();

      if (trimmed.startsWith('```')) {
        if (!inCode) {
          flushList();
          inCode = true;
          codeLang = trimmed.slice(3).trim();
          codeBuffer = [];
        } else {
          inCode = false;
          html += renderCodeBlock(codeBuffer.join('\n'), codeLang);
          codeLang = '';
          codeBuffer = [];
        }
        return;
      }

      if (inCode) {
        codeBuffer.push(line);
        return;
      }

      if (trimmed === '') {
        flushList();
        return;
      }

      if (trimmed.startsWith('- ')) {
        listBuffer.push(trimmed.slice(2));
        return;
      }

      flushList();

      if (trimmed.startsWith('# ')) {
        html += '<h1>' + renderInline(trimmed.slice(2), options) + '</h1>';
        return;
      }
      if (trimmed.startsWith('## ')) {
        html += '<h2>' + renderInline(trimmed.slice(3), options) + '</h2>';
        return;
      }
      if (trimmed.startsWith('### ')) {
        html += '<h3>' + renderInline(trimmed.slice(4), options) + '</h3>';
        return;
      }

      if (trimmed.startsWith('> ')) {
        html += '<blockquote>' + renderInline(trimmed.slice(2), options) + '</blockquote>';
        return;
      }

      html += '<p>' + renderInline(line, options) + '</p>';
    });

    flushList();

    if (inCode) {
      html += renderCodeBlock(codeBuffer.join('\n'), codeLang);
    }

    return html;
  };
})();
