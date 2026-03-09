/*
  목적: 참고자료(reference) payload 정규화 파서를 제공한다.
  설명: 다양한 입력 형식을 일관된 reference 구조로 변환하고 페이지 번호를 정규화한다.
  디자인 패턴: 파서 모듈 패턴
  참조: js/chat/cell/references.js, js/chat/cell/stream.js
*/
(function () {
  'use strict';

  window.App = window.App || {};

  function toPageNumber(rawValue) {
    var parsed = null;
    if (typeof rawValue === 'number') {
      parsed = rawValue;
    } else if (typeof rawValue === 'string' && rawValue.trim()) {
      parsed = Number(rawValue.trim());
    }
    if (typeof parsed !== 'number' || !isFinite(parsed)) {
      return null;
    }
    var normalized = Math.round(parsed);
    if (normalized < 0) {
      return null;
    }
    return normalized;
  }

  function normalizePageNumbers(rawValue) {
    var list = Array.isArray(rawValue) ? rawValue : [rawValue];
    var seen = {};
    var pageNumbers = [];

    list.forEach(function (value) {
      var pageNumber = toPageNumber(value);
      if (pageNumber === null) {
        return;
      }
      var key = String(pageNumber);
      if (seen[key]) {
        return;
      }
      seen[key] = true;
      pageNumbers.push(pageNumber);
    });

    pageNumbers.sort(function (left, right) {
      return left - right;
    });
    return pageNumbers;
  }

  function normalizeReference(item) {
    if (!item || typeof item !== 'object') {
      return null;
    }

    if (String(item.type || '').toLowerCase() === 'reference') {
      var metadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
      var pageSource = metadata.page_nums !== undefined ? metadata.page_nums : metadata.page_num;
      return {
        index: metadata.index !== undefined ? metadata.index : null,
        file_name: String(metadata.file_name || ''),
        file_path: String(metadata.file_path || ''),
        page_numbers: normalizePageNumbers(pageSource),
        score: metadata.score,
        snippet: metadata.snippet,
        body: typeof item.content === 'string' ? item.content : '',
        metadata: metadata
      };
    }

    var legacyMetadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
    var legacyPageSource = item.page_nums !== undefined
      ? item.page_nums
      : (
        item.page_num !== undefined
          ? item.page_num
          : (
            legacyMetadata.page_nums !== undefined
              ? legacyMetadata.page_nums
              : legacyMetadata.page_num
          )
      );
    return {
      index: item.index !== undefined ? item.index : legacyMetadata.index,
      file_name: String(item.file_name || legacyMetadata.file_name || ''),
      file_path: String(item.file_path || legacyMetadata.file_path || ''),
      page_numbers: normalizePageNumbers(legacyPageSource),
      score: item.score !== undefined ? item.score : legacyMetadata.score,
      snippet: item.snippet !== undefined ? item.snippet : legacyMetadata.snippet,
      body: typeof item.body === 'string' ? item.body : (typeof item.content === 'string' ? item.content : ''),
      metadata: legacyMetadata
    };
  }

  function parseReferences(value) {
    if (!value) {
      return [];
    }
    if (Array.isArray(value)) {
      var normalized = [];
      value.forEach(function (item) {
        var converted = normalizeReference(item);
        if (converted) {
          normalized.push(converted);
        }
      });
      return normalized;
    }
    if (typeof value === 'string') {
      var trimmed = value.trim();
      if (!trimmed) {
        return [];
      }
      try {
        return parseReferences(JSON.parse(trimmed));
      } catch (error) {
        return [];
      }
    }
    return [];
  }

  window.App.chatCellReferenceParser = {
    parse: parseReferences
  };
})();
