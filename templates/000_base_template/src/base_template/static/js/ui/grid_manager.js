/*
  목적: 채팅 그리드 및 확장 상태 관리
  설명: 최대 6개 셀 생성, 확장/복원 제어 제공
  디자인 패턴: 컨트롤러 모듈
  참조: js/chat/chat_cell.js
*/
(function () {
  'use strict';

  window.App = window.App || {};
  window.App.grid = window.App.grid || {};

  var cellCounter = 0;

  window.App.grid.init = function () {
    var grid = window.App.utils.qs('#chatGrid');
    var addBtn = window.App.utils.qs('#addCell');

    if (!grid || !addBtn) {
      return;
    }

    window.App.grid.gridEl = grid;
    window.App.grid.maxCells = 3;
    window.App.grid.cells = [];
    window.App.grid.expandedId = null;

    addBtn.addEventListener('click', function () {
      window.App.grid.addCell();
    });

    window.App.grid.addCell();

    window.addEventListener('resize', function () {
      window.App.grid.updateLayout();
    });
  };

  function getBaseColumns(count) {
    if (count <= 1) {
      return 1;
    }
    if (count === 2) {
      return 2;
    }
    return 3;
  }

  function getMaxColumnsByWidth() {
    var width = window.innerWidth;
    if (width <= 980) {
      return 1;
    }
    if (width <= 1100) {
      return 2;
    }
    return 3;
  }

  window.App.grid.updateLayout = function () {
    var grid = window.App.grid.gridEl;
    if (!grid) {
      return;
    }
    var count = window.App.grid.cells.length;
    var baseCols = getBaseColumns(count);
    var maxCols = getMaxColumnsByWidth();
    var cols = Math.min(baseCols, maxCols);
    if (cols < 1) {
      cols = 1;
    }
    var rows = 1;

    grid.style.gridTemplateColumns = 'repeat(' + cols + ', minmax(0, 1fr))';
    grid.style.gridTemplateRows = 'repeat(' + rows + ', minmax(0, 1fr))';
  };

  window.App.grid.updateCloseButtons = function () {
    var isMultiple = window.App.grid.cells.length > 1;
    window.App.grid.cells.forEach(function (cell) {
      var closeBtn = cell.element.querySelector('.btn-close');
      var expandBtn = cell.element.querySelector('.btn-expand');
      if (!closeBtn) {
        return;
      }
      if (isMultiple) {
        closeBtn.classList.remove('is-hidden');
        if (expandBtn) {
          expandBtn.classList.remove('is-hidden');
        }
      } else {
        closeBtn.classList.add('is-hidden');
        if (expandBtn) {
          expandBtn.classList.add('is-hidden');
        }
      }
    });
  };

  window.App.grid.updateAddButton = function () {
    var addBtn = window.App.utils.qs('#addCell');
    if (!addBtn) {
      return;
    }
    if (window.App.grid.cells.length >= window.App.grid.maxCells) {
      addBtn.classList.add('btn-disabled');
      addBtn.setAttribute('disabled', 'disabled');
      addBtn.setAttribute('aria-disabled', 'true');
    } else {
      addBtn.classList.remove('btn-disabled');
      addBtn.removeAttribute('disabled');
      addBtn.setAttribute('aria-disabled', 'false');
    }
  };

  window.App.grid.addCell = function () {
    if (!window.App.grid.gridEl) {
      return;
    }
    if (window.App.grid.cells.length >= window.App.grid.maxCells) {
      return;
    }

    cellCounter += 1;
    var cellId = 'cell-' + cellCounter;
    var title = '채팅 ' + cellCounter;
    var cellEl = window.App.chatCell.create(cellId, title);

    window.App.grid.gridEl.appendChild(cellEl);
    window.App.grid.cells.push({ id: cellId, title: title, element: cellEl });
    window.App.grid.updateLayout();
    window.App.grid.updateCloseButtons();
    window.App.grid.updateAddButton();

    if (window.App.app && window.App.app.onCellCreated) {
      window.App.app.onCellCreated(cellId, title);
    }
  };

  window.App.grid.removeCell = function (cellId) {
    if (window.App.grid.cells.length <= 1) {
      return;
    }

    var index = window.App.grid.cells.findIndex(function (cell) {
      return cell.id === cellId;
    });
    if (index === -1) {
      return;
    }

    var target = window.App.grid.cells[index];
    if (target.element && target.element.parentNode) {
      target.element.parentNode.removeChild(target.element);
    }
    window.App.grid.cells.splice(index, 1);

    if (window.App.grid.expandedId === cellId) {
      window.App.grid.clearExpanded();
    }

    window.App.grid.updateLayout();
    window.App.grid.updateCloseButtons();
    window.App.grid.updateAddButton();

    if (window.App.app && window.App.app.removeHistory) {
      window.App.app.removeHistory(cellId);
    }
  };

  window.App.grid.setExpanded = function (cellId) {
    var grid = window.App.grid.gridEl;
    if (!grid) {
      return;
    }

    window.App.grid.expandedId = cellId;
    grid.classList.add('is-expanded');

    window.App.grid.cells.forEach(function (cell) {
      if (cell.id === cellId) {
        cell.element.classList.add('is-expanded');
      } else {
        cell.element.classList.remove('is-expanded');
      }
    });
  };

  window.App.grid.clearExpanded = function () {
    var grid = window.App.grid.gridEl;
    if (!grid) {
      return;
    }

    window.App.grid.expandedId = null;
    grid.classList.remove('is-expanded');

    window.App.grid.cells.forEach(function (cell) {
      cell.element.classList.remove('is-expanded');
    });
  };
})();
