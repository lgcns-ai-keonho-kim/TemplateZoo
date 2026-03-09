/*
  목적: 앱 초기화 및 전역 상태 관리
  설명: 히스토리 패널(세션 이동/삭제)과 그리드, 테마 모듈을 연결
  디자인 패턴: 퍼사드 패턴
  참조: js/ui/*, js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.app = window.App.app || {};

  var state = {
    history: {}
  };

  function setActiveHistory(cellId) {
    var items = window.App.utils.qsa('.history-item');
    items.forEach(function (item) {
      if (item.getAttribute('data-cell-id') === cellId) {
        item.classList.add('is-active');
      } else {
        item.classList.remove('is-active');
      }
    });
  }

  window.App.app.setActiveHistory = setActiveHistory;


  window.App.app.onCellCreated = function (cellId, title, preview) {
    var list = window.App.utils.qs('#historyList');
    if (!list) {
      return;
    }

    var existing = window.App.utils.qs('.history-item[data-cell-id="' + cellId + '"]');
    if (existing) {
      var existingTitle = existing.querySelector('.history-title');
      var existingPreview = existing.querySelector('.history-preview');
      if (existingTitle && title && title.trim()) {
        existingTitle.textContent = title;
      }
      if (existingPreview) {
        existingPreview.textContent = preview && preview.trim().length > 0 ? preview : '대기 중';
      }
      state.history[cellId] = {
        title: title,
        preview: preview && preview.trim().length > 0 ? preview : '대기 중'
      };
      return;
    }

    var item = window.App.utils.createEl('li', 'history-item');
    item.setAttribute('data-cell-id', cellId);

    var itemHeader = window.App.utils.createEl('div', 'history-item__header');
    var itemTitle = window.App.utils.createEl('div', 'history-title');
    itemTitle.textContent = title;
    var deleteButton = window.App.utils.createEl('button', 'history-delete-btn');
    deleteButton.type = 'button';
    deleteButton.setAttribute('title', '채팅 삭제');
    deleteButton.setAttribute('aria-label', '채팅 삭제');
    var deleteIcon = window.App.utils.createEl('img', 'icon');
    deleteIcon.setAttribute('src', 'asset/icons/delete.svg');
    deleteIcon.setAttribute('alt', '');
    deleteButton.appendChild(deleteIcon);
    itemHeader.appendChild(itemTitle);
    itemHeader.appendChild(deleteButton);

    var itemPreview = window.App.utils.createEl('div', 'history-preview');
    itemPreview.textContent = preview && preview.trim().length > 0 ? preview : '대기 중';

    item.appendChild(itemHeader);
    item.appendChild(itemPreview);
    list.appendChild(item);

    state.history[cellId] = {
      title: title,
      preview: preview && preview.trim().length > 0 ? preview : '대기 중'
    };

    item.addEventListener('click', function () {
      setActiveHistory(cellId);
      if (window.App.grid && typeof window.App.grid.activateSession === 'function') {
        window.App.grid.activateSession(cellId);
      }
    });

    deleteButton.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (!window.confirm('이 채팅 세션을 삭제하시겠습니까?')) {
        return;
      }
      if (window.App.grid && typeof window.App.grid.deleteSession === 'function') {
        window.App.grid.deleteSession(cellId);
      }
    });

    if (Object.keys(state.history).length === 1) {
      setActiveHistory(cellId);
    }
  };

  window.App.app.updateHistory = function (cellId, title, preview) {
    var listItem = window.App.utils.qs('.history-item[data-cell-id="' + cellId + '"]');
    if (!listItem) {
      return;
    }

    var titleEl = listItem.querySelector('.history-title');
    var previewEl = listItem.querySelector('.history-preview');

    if (title && title.trim().length > 0) {
      titleEl.textContent = title;
    }

    if (preview && preview.trim().length > 0) {
      previewEl.textContent = preview.trim().slice(0, 60);
    }
  };

  window.App.app.removeHistory = function (cellId) {
    var listItem = window.App.utils.qs('.history-item[data-cell-id="' + cellId + '"]');
    if (!listItem) {
      return;
    }

    var wasActive = listItem.classList.contains('is-active');
    if (listItem.parentNode) {
      listItem.parentNode.removeChild(listItem);
    }
    delete state.history[cellId];

    if (wasActive) {
      var nextItem = window.App.utils.qs('.history-item');
      if (nextItem) {
        nextItem.classList.add('is-active');
      }
    }
  };

  window.App.app.bootstrap = function () {
    window.App.theme.init();
    window.App.panelToggle.init();
    window.App.grid.init();
  };
})();
