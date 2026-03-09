/*
  목적: 제한된 HTML 판별, 정제, 평문 추출 유틸을 제공한다.
  설명: assistant 응답과 참고자료 렌더링에 필요한 최소 HTML 안전 처리만 담당한다.
  디자인 패턴: 함수형 유틸 모듈
  참조: js/chat/chat_presenter.js, js/chat/cell/reference_view.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.html = window.App.html || {};

  var ALLOWED_HTML_TAGS = {
    A: true,
    P: true,
    BR: true,
    STRONG: true,
    EM: true,
    CODE: true,
    PRE: true,
    UL: true,
    OL: true,
    LI: true,
    BLOCKQUOTE: true,
    H1: true,
    H2: true,
    H3: true,
    H4: true,
    H5: true,
    H6: true,
    TABLE: true,
    THEAD: true,
    TBODY: true,
    TR: true,
    TH: true,
    TD: true,
    SPAN: true,
    DIV: true
  };
  var STREAMING_HTML_TAG_PATTERN = /<(table|thead|tbody|tr|th|td|p|ul|ol|li|div|blockquote|h[1-6]|pre|code|strong|em|br)\b/i;

  window.App.html.isLikelyHtml = function (raw) {
    var text = String(raw || '').trim();
    if (!text) {
      return false;
    }
    return /<\/?[a-z][\s\S]*>/i.test(text);
  };

  window.App.html.findStreamingHtmlStart = function (raw) {
    var text = String(raw || '');
    if (!text) {
      return -1;
    }
    var match = STREAMING_HTML_TAG_PATTERN.exec(text);
    if (!match || typeof match.index !== 'number') {
      return -1;
    }
    return match.index;
  };

  window.App.html.shouldBufferAssistantHtml = function (raw) {
    return window.App.html.findStreamingHtmlStart(raw) >= 0;
  };

  window.App.html.sanitizeLimitedHtml = function (rawHtml) {
    var template = document.createElement('template');
    template.innerHTML = String(rawHtml || '');

    function sanitizeNode(node) {
      if (!node || !node.childNodes) {
        return;
      }
      var children = Array.prototype.slice.call(node.childNodes);
      children.forEach(function (child) {
        if (child.nodeType === Node.TEXT_NODE) {
          return;
        }
        if (child.nodeType !== Node.ELEMENT_NODE) {
          child.remove();
          return;
        }

        var tagName = String(child.tagName || '').toUpperCase();
        if (!ALLOWED_HTML_TAGS[tagName]) {
          var replacement = document.createTextNode(child.textContent || '');
          child.parentNode.replaceChild(replacement, child);
          return;
        }

        var attributes = Array.prototype.slice.call(child.attributes || []);
        attributes.forEach(function (attribute) {
          var name = String(attribute.name || '').toLowerCase();
          var value = String(attribute.value || '');

          if (name.indexOf('on') === 0) {
            child.removeAttribute(attribute.name);
            return;
          }

          if (tagName === 'A') {
            if (name === 'href') {
              if (value.toLowerCase().indexOf('javascript:') === 0) {
                child.removeAttribute(attribute.name);
                return;
              }
              child.setAttribute('target', '_blank');
              child.setAttribute('rel', 'noopener noreferrer');
              return;
            }
            if (name === 'title' || name === 'target' || name === 'rel') {
              return;
            }
            child.removeAttribute(attribute.name);
            return;
          }

          if (name === 'class') {
            return;
          }
          child.removeAttribute(attribute.name);
        });

        sanitizeNode(child);
      });
    }

    sanitizeNode(template.content);
    return template.innerHTML;
  };

  window.App.html.extractPlainText = function (rawHtml) {
    var template = document.createElement('template');
    template.innerHTML = window.App.html.sanitizeLimitedHtml(rawHtml);
    return String(template.content.textContent || '')
      .replace(/\s+/g, ' ')
      .trim();
  };
})();
