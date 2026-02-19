/*
  목적: DOM 조작 및 공통 유틸 제공
  설명: 쿼리, 엘리먼트 생성, 문자열 이스케이프 등을 단일 모듈로 제공
  디자인 패턴: 모듈 패턴
  참조: js/utils/markdown.js, js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.utils = window.App.utils || {};

  /** @param {string} selector */
  window.App.utils.qs = function (selector, scope) {
    return (scope || document).querySelector(selector);
  };

  /** @param {string} selector */
  window.App.utils.qsa = function (selector, scope) {
    return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
  };

  /** @param {string} tagName */
  window.App.utils.createEl = function (tagName, className) {
    var el = document.createElement(tagName);
    if (className) {
      el.className = className;
    }
    return el;
  };

  /** @param {string} value */
  window.App.utils.escapeHtml = function (value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  /** @param {number} value */
  window.App.utils.clamp = function (value, min, max) {
    return Math.min(Math.max(value, min), max);
  };

  window.App.utils.formatTime = function () {
    var now = new Date();
    var hours = now.getHours().toString().padStart(2, '0');
    var minutes = now.getMinutes().toString().padStart(2, '0');
    return hours + ':' + minutes;
  };
})();
