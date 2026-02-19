/*
  목적: 앱 부트스트랩 실행
  설명: 모듈 로딩 후 초기화를 수행
  디자인 패턴: 초기화 스크립트
  참조: js/core/app.js
*/
(function () {
  'use strict';

  if (window.App && window.App.app && window.App.app.bootstrap) {
    window.App.app.bootstrap();
  }
})();
