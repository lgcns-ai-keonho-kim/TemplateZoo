/*
  목적: 문법 강조의 공통 처리 로직 제공
  설명: 언어 등록, 별칭 처리, 기본 토큰 하이라이팅을 수행
  디자인 패턴: 레지스트리 기반 전략 패턴
  참조: js/utils/dom.js, js/utils/syntax_highlighting/languages/*
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.syntax = window.App.syntax || {};

  var registry = window.App.syntax._registry || {
    languages: {},
    aliases: {}
  };
  window.App.syntax._registry = registry;

  function escapeRegex(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  window.App.syntax.registerLanguage = function (name, keywords, commentPrefix, aliases) {
    if (!name) {
      return;
    }
    registry.languages[name] = {
      keywords: keywords || [],
      commentPrefix: commentPrefix || ''
    };
    if (Array.isArray(aliases)) {
      aliases.forEach(function (alias) {
        registry.aliases[String(alias).toLowerCase()] = name;
      });
    }
  };

  window.App.syntax.resolveLang = function (lang) {
    var value = String(lang || '').toLowerCase();
    return registry.aliases[value] || value;
  };

  function splitComment(line, lang) {
    var config = registry.languages[lang];
    var prefix = config ? config.commentPrefix : '';
    if (!prefix) {
      return { code: line, comment: '' };
    }
    var index = line.indexOf(prefix);
    if (index === -1) {
      return { code: line, comment: '' };
    }
    return { code: line.slice(0, index), comment: line.slice(index) };
  }

  function highlightInline(text, lang) {
    var escaped = window.App.utils.escapeHtml(text);
    escaped = escaped.replace(/("[^"\n]*"|'[^'\n]*')/g, '<span class="token-str">$1</span>');
    escaped = escaped.replace(/\b\d+(\.\d+)?\b/g, '<span class="token-num">$&</span>');

    var config = registry.languages[lang];
    var keywords = config ? config.keywords : [];
    if (keywords.length > 0) {
      var pattern = keywords.map(escapeRegex).join('|');
      var keywordRegex = new RegExp('\\b(' + pattern + ')\\b', 'gi');
      escaped = escaped.replace(keywordRegex, '<span class="token-kw">$1</span>');
    }

    return escaped;
  }

  window.App.syntax.highlight = function (code, lang) {
    var normalized = window.App.syntax.resolveLang(lang);
    var lines = String(code).replace(/\r\n/g, '\n').split('\n');
    var highlighted = lines
      .map(function (line) {
        var parts = splitComment(line, normalized);
        var base = highlightInline(parts.code, normalized);
        if (parts.comment) {
          base += '<span class="token-com">' + window.App.utils.escapeHtml(parts.comment) + '</span>';
        }
        return base;
      })
      .join('\n');

    return highlighted;
  };
})();
