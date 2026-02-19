/*
  목적: 좌측 패널 접기/펴기 토글 제공
  설명: 고정 폭 패널을 버튼으로 접고 펴는 기능을 수행
  디자인 패턴: 상태 캡슐화 모듈
  참조: css/main.css, index.html
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.panelToggle = window.App.panelToggle || {};

  var STORAGE_KEY = 'chatbot-panel-collapsed';

  function applyState(isCollapsed) {
    var panel = window.App.utils.qs('#sidePanel');
    var btn = window.App.utils.qs('#panelToggle');
    var icon = btn ? btn.querySelector('img') : null;
    if (!panel || !btn) {
      return;
    }

    if (isCollapsed) {
      panel.classList.add('is-collapsed');
      btn.setAttribute('aria-label', '패널 펴기');
      btn.setAttribute('title', '패널 펴기');
      if (icon) {
        icon.setAttribute('src', 'asset/icons/left_panel_open.svg');
      }
    } else {
      panel.classList.remove('is-collapsed');
      btn.setAttribute('aria-label', '패널 접기');
      btn.setAttribute('title', '패널 접기');
      if (icon) {
        icon.setAttribute('src', 'asset/icons/left_panel_close.svg');
      }
    }
  }

  window.App.panelToggle.init = function () {
    var btn = window.App.utils.qs('#panelToggle');
    if (!btn) {
      return;
    }

    var saved = localStorage.getItem(STORAGE_KEY);
    var isCollapsed = saved === 'true';
    applyState(isCollapsed);

    btn.addEventListener('click', function () {
      var panel = window.App.utils.qs('#sidePanel');
      if (!panel) {
        return;
      }
      var nextState = !panel.classList.contains('is-collapsed');
      localStorage.setItem(STORAGE_KEY, String(nextState));
      applyState(nextState);
    });
  };
})();
