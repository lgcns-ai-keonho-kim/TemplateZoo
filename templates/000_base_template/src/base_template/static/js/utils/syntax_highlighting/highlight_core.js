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

  function findCommentIndex(line, prefix) {
    if (!prefix) {
      return -1;
    }

    var inQuote = '';
    for (var i = 0; i < line.length; i += 1) {
      var ch = line.charAt(i);
      if (inQuote) {
        if (ch === '\\') {
          i += 1;
          continue;
        }
        if (ch === inQuote) {
          inQuote = '';
        }
        continue;
      }

      if (ch === '"' || ch === '\'') {
        inQuote = ch;
        continue;
      }

      if (line.slice(i, i + prefix.length) === prefix) {
        return i;
      }
    }

    return -1;
  }

  function splitComment(line, lang) {
    var config = registry.languages[lang];
    var prefix = config ? config.commentPrefix : '';
    if (!prefix) {
      return { code: line, comment: '' };
    }
    var index = findCommentIndex(line, prefix);
    if (index === -1) {
      return { code: line, comment: '' };
    }
    return { code: line.slice(0, index), comment: line.slice(index) };
  }

  function isIdentifierStart(ch) {
    return /[A-Za-z_]/.test(ch);
  }

  function isIdentifierPart(ch) {
    return /[A-Za-z0-9_]/.test(ch);
  }

  function isDigit(ch) {
    return /[0-9]/.test(ch);
  }

  function readStringToken(text, startIndex) {
    var quote = text.charAt(startIndex);
    var index = startIndex + 1;
    while (index < text.length) {
      var ch = text.charAt(index);
      if (ch === '\\') {
        index += 2;
        continue;
      }
      index += 1;
      if (ch === quote) {
        break;
      }
    }
    return { token: text.slice(startIndex, index), nextIndex: index };
  }

  function readIdentifierToken(text, startIndex) {
    var index = startIndex;
    while (index < text.length && isIdentifierPart(text.charAt(index))) {
      index += 1;
    }
    return { token: text.slice(startIndex, index), nextIndex: index };
  }

  function readNumberToken(text, startIndex) {
    var index = startIndex;
    while (index < text.length && isDigit(text.charAt(index))) {
      index += 1;
    }
    if (
      index < text.length &&
      text.charAt(index) === '.' &&
      index + 1 < text.length &&
      isDigit(text.charAt(index + 1))
    ) {
      index += 1;
      while (index < text.length && isDigit(text.charAt(index))) {
        index += 1;
      }
    }
    return { token: text.slice(startIndex, index), nextIndex: index };
  }

  function highlightInline(text, lang) {
    var config = registry.languages[lang];
    var keywords = config ? config.keywords : [];
    var keywordSet = {};
    keywords.forEach(function (keyword) {
      keywordSet[String(keyword).toLowerCase()] = true;
    });

    var source = String(text || '');
    var html = '';
    var index = 0;
    while (index < source.length) {
      var ch = source.charAt(index);

      if (ch === '"' || ch === '\'') {
        var stringToken = readStringToken(source, index);
        html += '<span class="token-str">' + window.App.utils.escapeHtml(stringToken.token) + '</span>';
        index = stringToken.nextIndex;
        continue;
      }

      if (isDigit(ch)) {
        var prev = index > 0 ? source.charAt(index - 1) : '';
        if (!isIdentifierPart(prev)) {
          var numberToken = readNumberToken(source, index);
          html += '<span class="token-num">' + window.App.utils.escapeHtml(numberToken.token) + '</span>';
          index = numberToken.nextIndex;
          continue;
        }
      }

      if (isIdentifierStart(ch)) {
        var wordToken = readIdentifierToken(source, index);
        var normalized = wordToken.token.toLowerCase();
        if (keywordSet[normalized]) {
          html += '<span class="token-kw">' + window.App.utils.escapeHtml(wordToken.token) + '</span>';
        } else {
          html += window.App.utils.escapeHtml(wordToken.token);
        }
        index = wordToken.nextIndex;
        continue;
      }

      html += window.App.utils.escapeHtml(ch);
      index += 1;
    }

    return html;
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
