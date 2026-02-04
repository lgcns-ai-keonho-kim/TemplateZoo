/*
  목적: 라이트/다크 테마 토글 제공
  설명: 로컬 스토리지 기반 테마 상태를 적용
  디자인 패턴: 상태 캡슐화 모듈
  참조: css/main.css, index.html
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.theme = window.App.theme || {};

  var STORAGE_KEY = 'base-template-theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  function updateButton(theme) {
    var btn = window.App.utils.qs('#themeToggle');
    if (!btn) {
      return;
    }
    var icon = btn.querySelector('img');
    if (theme === 'dark') {
      if (icon) {
        icon.setAttribute('src', 'asset/icons/sun.svg');
      }
      btn.setAttribute('aria-label', '라이트 모드');
      btn.setAttribute('title', '라이트 모드');
    } else {
      if (icon) {
        icon.setAttribute('src', 'asset/icons/moon.svg');
      }
      btn.setAttribute('aria-label', '다크 모드');
      btn.setAttribute('title', '다크 모드');
    }
  }

  window.App.theme.init = function () {
    var saved = localStorage.getItem(STORAGE_KEY) || 'light';
    applyTheme(saved);
    updateButton(saved);

    var btn = window.App.utils.qs('#themeToggle');
    if (!btn) {
      return;
    }

    btn.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      var nextTheme = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEY, nextTheme);
      applyTheme(nextTheme);
      updateButton(nextTheme);
    });
  };
})();
