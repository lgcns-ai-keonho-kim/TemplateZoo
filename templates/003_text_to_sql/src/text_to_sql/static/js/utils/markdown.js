/*
  목적: 간단한 마크다운 렌더링 제공
  설명: 제목, 리스트, 인라인 강조, 코드 블록 등 핵심 기능만 지원 (입력 HTML은 이스케이프 처리)
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
    var escaped = escapeHtml(raw);
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
  function renderCodeBlock(code, language, options) {
    var disableSyntaxHighlight = Boolean(options && options.disableSyntaxHighlight);
    var highlighted = disableSyntaxHighlight
      ? escapeHtml(code)
      : window.App.syntax.highlight(code, language);
    var langClass = language ? ' language-' + escapeHtml(language) : '';
    return '<pre><code class="' + langClass + '">' + highlighted + '</code></pre>';
  }

  /**
   * 모델 출력 뒤에 붙는 구조화 조각(`[{'type': 'text', ...}]`) 아티팩트를 제거한다.
   * @param {string} rawText
   * @returns {string}
   */
  function stripStructuredTailArtifact(rawText) {
    var source = String(rawText || '');
    var trimmed = source.replace(/\s+$/, '');
    var start = trimmed.lastIndexOf('[');
    if (start < 0) {
      return source;
    }

    var tail = trimmed.slice(start);
    if (!/^\[\s*\{/.test(tail)) {
      return source;
    }
    if (!/(?:'|")type(?:'|")\s*:\s*(?:'|")text(?:'|")/.test(tail)) {
      return source;
    }
    if (!/(?:'|")text(?:'|")\s*:/.test(tail)) {
      return source;
    }

    return trimmed.slice(0, start).replace(/\s+$/, '');
  }

  /**
   * 코드 펜스(```lang / ```) 라인을 판별한다.
   * @param {string} trimmedLine
   * @returns {{language: string} | null}
   */
  function parseFenceLine(trimmedLine) {
    var match = /^```([A-Za-z0-9_+-]*)?\s*$/.exec(trimmedLine);
    if (!match) {
      return null;
    }
    var language = String(match[1] || '').trim();
    return { language: language };
  }

  /** @param {string} text */
  window.App.markdown.render = function (text, options) {
    var normalized = stripStructuredTailArtifact(String(text || '')).replace(/\r\n/g, '\n');
    var lines = normalized.split('\n');
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
      var fence = parseFenceLine(trimmed);

      if (!inCode && fence) {
        flushList();
        inCode = true;
        codeLang = String(fence.language || '');
        codeBuffer = [];
        return;
      }

      if (inCode && fence) {
        inCode = false;
        html += renderCodeBlock(codeBuffer.join('\n'), codeLang, options);
        codeLang = '';
        codeBuffer = [];
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

      var headingMatch = /^(#{1,6})\s+(.+)$/.exec(trimmed);
      if (headingMatch) {
        var headingLevel = headingMatch[1].length;
        var headingText = headingMatch[2];
        html += '<h' + headingLevel + '>' + renderInline(headingText, options) + '</h' + headingLevel + '>';
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
      html += renderCodeBlock(codeBuffer.join('\n'), codeLang, options);
    }

    return html;
  };
})();
