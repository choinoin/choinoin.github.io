/* 자료 열람 잠금: 파일(PDF 등)을 열기 전에 코드(cclab)를 입력. 맞으면 이 브라우저에 기억.
   공개 저장소를 직접 아는 사람은 우회 가능 — 강의 수강생 편의를 위한 가벼운 장치입니다. */
(function () {
  "use strict";
  var KEY = 'cclab-unlock', CODE = 'cclab', TTL = 10 * 60 * 1000; // 유효 1시간
  var modal, input, err, cb = null;
  window.cclabUnlocked = function () {
    try {
      var t = parseInt(localStorage.getItem(KEY), 10);
      if (t && (Date.now() - t) < TTL) return true;
      if (t) localStorage.removeItem(KEY); // 만료분 정리
      return false;
    } catch (e) { return false; }
  };

  function ensure() {
    if (modal) return;
    modal = document.createElement('div'); modal.id = 'gate-modal'; modal.hidden = true;
    modal.innerHTML =
      '<div class="gate-back" data-gclose></div>' +
      '<div class="gate-box" role="dialog" aria-modal="true">' +
      '<h3>자료 열람 코드</h3>' +
      '<p>강의에서 안내한 코드를 입력하면 자료를 볼 수 있습니다.</p>' +
      '<input type="text" id="gate-input" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="코드 입력">' +
      '<p class="gate-err" id="gate-err" hidden>코드가 올바르지 않습니다.</p>' +
      '<div class="gate-btns"><button type="button" class="btn-ghost" data-gclose>취소</button>' +
      '<button type="button" class="btn" id="gate-ok">확인</button></div></div>';
    document.body.appendChild(modal);
    input = modal.querySelector('#gate-input'); err = modal.querySelector('#gate-err');
    function close() { modal.hidden = true; err.hidden = true; input.value = ''; cb = null; }
    function submit() {
      if (input.value.trim().toLowerCase() === CODE) {
        try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
        var f = cb; close(); if (f) f();
      } else { err.hidden = false; input.focus(); input.select(); }
    }
    modal.querySelector('#gate-ok').addEventListener('click', submit);
    modal.addEventListener('click', function (e) { if (e.target.hasAttribute('data-gclose')) close(); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); else if (e.key === 'Escape') close(); });
  }

  window.cclabAsk = function (onOK) {
    if (window.cclabUnlocked()) { if (onOK) onOK(); return; }
    ensure(); cb = onOK; modal.hidden = false; setTimeout(function () { input.focus(); }, 30);
  };

  // 파일 링크 클릭 가로채기 (논문 PDF, 첨부 다운로드 등)
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('a'); if (!a) return;
    var href = a.getAttribute('href') || '';
    // 실제 파일 링크만 잠근다 (페이지 이동 링크는 제외)
    var isFile = a.classList.contains('pdf-link') || a.hasAttribute('download') || /\.(pdf|pptx?|docx?|hwp|zip|xlsx?)($|\?)/i.test(href);
    if (!isFile || window.cclabUnlocked()) return;
    ev.preventDefault(); ev.stopPropagation();
    window.cclabAsk(function () { a.click(); });
  }, true);
})();
