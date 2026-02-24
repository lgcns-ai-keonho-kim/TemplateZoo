/*
  목적: 참고자료(reference) UI 렌더링을 제공한다.
  설명: 모달 렌더링과 캐러셀 버튼/드래그 이동 로직을 관리한다.
  디자인 패턴: 컴포넌트 뷰 모듈
  참조: js/chat/cell/references.js, js/utils/markdown.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  var REFERENCE_MODAL_ID = 'referenceModal';
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

  function sanitizeLimitedHtml(rawHtml) {
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
  }

  function ensureReferenceModal() {
    var existing = window.App.utils.qs('#' + REFERENCE_MODAL_ID);
    if (existing) {
      return existing;
    }

    var modal = window.App.utils.createEl('div', 'reference-modal is-hidden');
    modal.id = REFERENCE_MODAL_ID;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');

    var overlay = window.App.utils.createEl('div', 'reference-modal__overlay');
    var panel = window.App.utils.createEl('div', 'reference-modal__panel');
    var header = window.App.utils.createEl('div', 'reference-modal__header');
    var title = window.App.utils.createEl('h3', 'reference-modal__title');
    var closeBtn = window.App.utils.createEl('button', 'reference-modal__close');
    closeBtn.type = 'button';
    closeBtn.textContent = '닫기';

    var meta = window.App.utils.createEl('div', 'reference-modal__meta');
    var bodyWrap = window.App.utils.createEl('div', 'reference-modal__body');

    header.appendChild(title);
    header.appendChild(closeBtn);
    panel.appendChild(header);
    panel.appendChild(meta);
    panel.appendChild(bodyWrap);
    modal.appendChild(overlay);
    modal.appendChild(panel);

    function closeModal() {
      modal.classList.add('is-hidden');
      modal.classList.remove('is-visible');
    }

    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);

    document.body.appendChild(modal);
    return modal;
  }

  function openReferenceModal(reference) {
    var modal = ensureReferenceModal();
    var titleEl = modal.querySelector('.reference-modal__title');
    var metaEl = modal.querySelector('.reference-modal__meta');
    var bodyEl = modal.querySelector('.reference-modal__body');
    if (!titleEl || !metaEl || !bodyEl) {
      return;
    }

    titleEl.textContent = String(reference.file_name || '참고자료');
    metaEl.innerHTML = '';

    function appendMeta(label, value) {
      var text = String(value || '').trim();
      if (!text) {
        return;
      }
      var row = window.App.utils.createEl('div', 'reference-meta-row');
      row.textContent = label + ': ' + text;
      metaEl.appendChild(row);
    }

    appendMeta('파일 경로', reference.file_path);
    appendMeta('점수', reference.score);
    if (Array.isArray(reference.page_numbers) && reference.page_numbers.length > 0) {
      appendMeta('페이지', reference.page_numbers.join(', '));
    }
    appendMeta('미리보기', reference.snippet);

    if (reference.metadata && typeof reference.metadata === 'object') {
      var metadataRow = window.App.utils.createEl('div', 'reference-meta-row');
      metadataRow.textContent = '메타데이터: ' + JSON.stringify(reference.metadata, null, 2);
      metaEl.appendChild(metadataRow);
    }

    var markdownHtml = window.App.markdown.render(String(reference.body || ''));
    bodyEl.innerHTML = '<div class="markdown">' + sanitizeLimitedHtml(markdownHtml) + '</div>';

    modal.classList.remove('is-hidden');
    modal.classList.add('is-visible');
  }

  function renderReferencesCarousel(container, references) {
    if (!container) {
      return;
    }
    var old = container.querySelector('.references-carousel');
    if (old) {
      old.remove();
    }
    if (!Array.isArray(references) || references.length === 0) {
      return;
    }

    var wrapper = window.App.utils.createEl('div', 'references-carousel');
    var headerEl = window.App.utils.createEl('div', 'references-carousel__header');
    var titleEl = window.App.utils.createEl('div', 'references-carousel__title');
    titleEl.textContent = '참고 자료';
    headerEl.appendChild(titleEl);

    var controlsEl = window.App.utils.createEl('div', 'references-carousel__controls');
    var prevBtn = window.App.utils.createEl('button', 'references-carousel__nav references-carousel__nav--prev');
    prevBtn.type = 'button';
    prevBtn.setAttribute('aria-label', '이전 참고 자료 보기');
    var prevIcon = window.App.utils.createEl('img', 'references-carousel__nav-icon');
    prevIcon.setAttribute('src', 'asset/icons/carousel_arrow_left.svg');
    prevIcon.setAttribute('alt', '');
    prevBtn.appendChild(prevIcon);

    var nextBtn = window.App.utils.createEl('button', 'references-carousel__nav references-carousel__nav--next');
    nextBtn.type = 'button';
    nextBtn.setAttribute('aria-label', '다음 참고 자료 보기');
    var nextIcon = window.App.utils.createEl('img', 'references-carousel__nav-icon');
    nextIcon.setAttribute('src', 'asset/icons/carousel_arrow_right.svg');
    nextIcon.setAttribute('alt', '');
    nextBtn.appendChild(nextIcon);
    controlsEl.appendChild(prevBtn);
    controlsEl.appendChild(nextBtn);
    headerEl.appendChild(controlsEl);
    wrapper.appendChild(headerEl);

    var bodyEl = window.App.utils.createEl('div', 'references-carousel__body');

    var viewport = window.App.utils.createEl('div', 'references-carousel__viewport');
    var track = window.App.utils.createEl('div', 'references-carousel__track');
    viewport.appendChild(track);
    bodyEl.appendChild(viewport);
    wrapper.appendChild(bodyEl);

    var NAV_EDGE_EPSILON_PX = 1;
    var DRAG_CLICK_THRESHOLD_PX = 6;
    var DRAG_SNAP_TRIGGER_RATIO = 0.16;
    var DRAG_SNAP_TRIGGER_MIN_PX = 28;
    var DRAG_SNAP_TRIGGER_MAX_PX = 120;
    var DRAG_SNAP_EPSILON_PX = 2;
    var suppressTimerId = null;
    var dragState = {
      active: false,
      startX: 0,
      startScrollLeft: 0,
      moved: false,
      suppressClick: false
    };

    function getMaxScrollLeft() {
      return Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    }

    function clampScrollLeft(value) {
      var maxScrollLeft = getMaxScrollLeft();
      return Math.max(0, Math.min(maxScrollLeft, value));
    }

    function getPageWidth() {
      return Math.max(1, viewport.clientWidth);
    }

    function updateNavButtons() {
      var maxScrollLeft = getMaxScrollLeft();
      var current = viewport.scrollLeft;
      prevBtn.disabled = current <= NAV_EDGE_EPSILON_PX;
      nextBtn.disabled = current >= (maxScrollLeft - NAV_EDGE_EPSILON_PX);
    }

    function scrollToLeft(left, smooth) {
      var target = clampScrollLeft(left);
      if (smooth && typeof viewport.scrollTo === 'function') {
        viewport.scrollTo({ left: target, behavior: 'smooth' });
      } else {
        viewport.scrollLeft = target;
      }
      updateNavButtons();
    }

    function scrollByPage(direction) {
      var pageWidth = getPageWidth();
      var target = clampScrollLeft(viewport.scrollLeft + (direction * pageWidth));
      if (Math.abs(target - viewport.scrollLeft) <= NAV_EDGE_EPSILON_PX) {
        updateNavButtons();
        return;
      }
      scrollToLeft(target, true);
    }

    function snapToPage(pageIndex) {
      var pageWidth = getPageWidth();
      var maxScrollLeft = getMaxScrollLeft();
      var maxPageIndex = Math.ceil(maxScrollLeft / pageWidth);
      var safePageIndex = Math.max(0, Math.min(maxPageIndex, pageIndex));
      var target = Math.min(maxScrollLeft, Math.max(0, safePageIndex * pageWidth));
      scrollToLeft(target, true);
    }

    function getDragSnapTriggerPx(pageWidth) {
      var computed = pageWidth * DRAG_SNAP_TRIGGER_RATIO;
      return Math.max(DRAG_SNAP_TRIGGER_MIN_PX, Math.min(DRAG_SNAP_TRIGGER_MAX_PX, computed));
    }

    function snapByDragDistance() {
      var pageWidth = getPageWidth();
      var delta = viewport.scrollLeft - dragState.startScrollLeft;
      var trigger = getDragSnapTriggerPx(pageWidth);
      var startPageIndex = Math.round(dragState.startScrollLeft / pageWidth);
      if (Math.abs(delta) <= (trigger + DRAG_SNAP_EPSILON_PX)) {
        snapToPage(startPageIndex);
        return;
      }
      var direction = delta > 0 ? 1 : -1;
      snapToPage(startPageIndex + direction);
    }

    function clearSuppressTimer() {
      if (suppressTimerId !== null) {
        clearTimeout(suppressTimerId);
        suppressTimerId = null;
      }
    }

    function suppressCardClickTemporarily() {
      clearSuppressTimer();
      dragState.suppressClick = true;
      suppressTimerId = setTimeout(function () {
        dragState.suppressClick = false;
        suppressTimerId = null;
      }, 220);
    }

    function addGlobalPointerListeners() {
      window.addEventListener('pointerup', onPointerUp);
      window.addEventListener('pointercancel', onPointerUp);
    }

    function removeGlobalPointerListeners() {
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
    }

    function finishDrag(event) {
      if (!dragState.active) {
        return;
      }
      dragState.active = false;
      viewport.classList.remove('is-dragging');
      removeGlobalPointerListeners();

      if (dragState.moved) {
        suppressCardClickTemporarily();
        snapByDragDistance();
        return;
      }
      updateNavButtons();
    }

    function onPointerDown(event) {
      if (event.pointerType === 'mouse' && event.button !== 0) {
        return;
      }
      dragState.active = true;
      dragState.startX = event.clientX;
      dragState.startScrollLeft = viewport.scrollLeft;
      dragState.moved = false;
      viewport.classList.add('is-dragging');
      addGlobalPointerListeners();
    }

    function onPointerMove(event) {
      if (!dragState.active) {
        return;
      }
      var deltaX = event.clientX - dragState.startX;
      if (Math.abs(deltaX) > DRAG_CLICK_THRESHOLD_PX) {
        dragState.moved = true;
        event.preventDefault();
      }
      viewport.scrollLeft = clampScrollLeft(dragState.startScrollLeft - deltaX);
      updateNavButtons();
    }

    function onPointerUp(event) {
      finishDrag(event);
    }

    function alignToFirstPage() {
      scrollToLeft(0, false);
    }

    references.forEach(function (reference) {
      var card = window.App.utils.createEl('button', 'reference-card');
      card.type = 'button';

      var fileName = window.App.utils.createEl('div', 'reference-card__file');
      fileName.textContent = String(reference.file_name || 'unknown');
      card.appendChild(fileName);

      if (reference.file_path) {
        var pathEl = window.App.utils.createEl('div', 'reference-card__path');
        pathEl.textContent = String(reference.file_path);
        card.appendChild(pathEl);
      }

      if (reference.score !== undefined && reference.score !== null) {
        var scoreEl = window.App.utils.createEl('div', 'reference-card__score');
        scoreEl.textContent = 'score: ' + String(reference.score);
        card.appendChild(scoreEl);
      }

      if (Array.isArray(reference.page_numbers) && reference.page_numbers.length > 0) {
        var pageEl = window.App.utils.createEl('div', 'reference-card__page');
        pageEl.textContent = '페이지: ' + reference.page_numbers.join(', ');
        card.appendChild(pageEl);
      }

      var preview = window.App.utils.createEl('div', 'reference-card__preview');
      preview.textContent = String(reference.body || '').slice(0, 180);
      card.appendChild(preview);

      var detail = window.App.utils.createEl('div', 'reference-card__action');
      detail.textContent = '전문 보기';
      card.appendChild(detail);

      card.addEventListener('click', function () {
        if (dragState.suppressClick) {
          return;
        }
        openReferenceModal(reference);
      });
      track.appendChild(card);
    });

    prevBtn.addEventListener('click', function () {
      scrollByPage(-1);
    });
    nextBtn.addEventListener('click', function () {
      scrollByPage(1);
    });
    viewport.addEventListener('scroll', updateNavButtons);
    viewport.addEventListener('pointerdown', onPointerDown);
    viewport.addEventListener('pointermove', onPointerMove);
    viewport.addEventListener('pointerup', onPointerUp);
    viewport.addEventListener('pointercancel', onPointerUp);
    container.appendChild(wrapper);
    alignToFirstPage();
    if (typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(function () {
        alignToFirstPage();
      });
    }
    updateNavButtons();
  }

  window.App.chatCellReferenceView = {
    renderCarousel: renderReferencesCarousel
  };
})();
