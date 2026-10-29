/* 코드블록 구문 강조 초기화 (highlight.js). 모달·미리보기에서도 재사용되는 window.cclabHighlight 제공. */
(function () {
  "use strict";
  function hl(scope) {
    scope = scope || document;
    if (!window.hljs) return;
    var blocks = scope.querySelectorAll('pre code');
    for (var i = 0; i < blocks.length; i++) {
      var b = blocks[i];
      if (b.dataset.hl) continue;          // 중복 강조 방지
      try { window.hljs.highlightElement(b); b.dataset.hl = '1'; } catch (e) {}
    }
  }
  window.cclabHighlight = hl;
  if (document.readyState !== 'loading') hl();
  else document.addEventListener('DOMContentLoaded', function () { hl(); });
})();
