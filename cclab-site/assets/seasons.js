/* 계절 배경 애니메이션: 봄 꽃잎 · 여름 잎 · 가을 낙엽 · 겨울 눈.
   내용 위로 은은하게 흐릅니다(클릭은 통과). 우하단 토글로 켜고 끌 수 있고 선택은 기억됩니다.
   동작 최소화(prefers-reduced-motion) 설정 시 기본 꺼짐. */
(function () {
  "use strict";
  var KEY = 'cclab-season';
  function pref() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function setPref(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // 기본값: 동작최소화면 off, 아니면 on. 사용자가 선택했으면 그 값 우선.
  var saved = pref();
  var on = saved ? (saved === 'on') : !reduce;

  var month = new Date().getMonth() + 1;
  var season = (month >= 3 && month <= 5) ? 'spring'
    : (month >= 6 && month <= 8) ? 'summer'
    : (month >= 9 && month <= 11) ? 'autumn' : 'winter';
  var LABEL = { spring: '🌸', summer: '🍃', autumn: '🍁', winter: '❄️' }[season];
  var THEME = {
    spring: { kind: 'petal', colors: ['#f6b8cb', '#ef9fb8', '#f9c9d8'], alpha: 0.7, sizeMin: 5, sizeMax: 10, speed: 0.5 },
    summer: { kind: 'leaf',  colors: ['#7cb982', '#5c9e68', '#9ccb8e'], alpha: 0.55, sizeMin: 6, sizeMax: 11, speed: 0.45 },
    autumn: { kind: 'leaf',  colors: ['#c0572b', '#d98324', '#e0a13f', '#a8431f', '#9c6b2e'], alpha: 0.78, sizeMin: 7, sizeMax: 13, speed: 0.7 },
    winter: { kind: 'snow',  colors: ['#ffffff', '#eaf3fb', '#dceaf6'], alpha: 0.9, sizeMin: 2, sizeMax: 5, speed: 0.6 }
  }[season];

  var canvas, ctx, W, H, DPR, parts = [], raf = 0, running = false;

  function makeCanvas() {
    canvas = document.createElement('canvas');
    canvas.id = 'season-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    document.body.appendChild(canvas);
    ctx = canvas.getContext('2d');
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    resize();
    window.addEventListener('resize', resize);
    var COUNT = Math.max(16, Math.min(Math.round(W / 22), 54));
    parts = [];
    for (var i = 0; i < COUNT; i++) parts.push(spawn(true));
  }
  function resize() {
    if (!canvas) return;
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function spawn(top) {
    return { x: rand(0, W), y: top ? rand(-H, 0) : -10, s: rand(THEME.sizeMin, THEME.sizeMax),
      vy: rand(0.4, 1.3) * THEME.speed, sway: rand(0.4, 1.2), phase: rand(0, Math.PI * 2),
      rot: rand(0, Math.PI * 2), vr: rand(-0.02, 0.02),
      color: THEME.colors[(Math.random() * THEME.colors.length) | 0] };
  }
  function drawLeaf(s) { ctx.beginPath(); ctx.moveTo(0, -s); ctx.quadraticCurveTo(s, 0, 0, s); ctx.quadraticCurveTo(-s, 0, 0, -s); ctx.closePath(); ctx.fill(); }
  function frame() {
    if (!running) return;
    ctx.clearRect(0, 0, W, H);
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      p.phase += 0.01; p.y += p.vy; p.x += Math.sin(p.phase) * p.sway; p.rot += p.vr;
      if (p.y - p.s > H) { parts[i] = spawn(false); continue; }
      ctx.save(); ctx.globalAlpha = THEME.alpha; ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = p.color;
      if (THEME.kind === 'snow') { ctx.beginPath(); ctx.arc(0, 0, p.s, 0, Math.PI * 2); ctx.fill(); }
      else if (THEME.kind === 'petal') { ctx.beginPath(); ctx.ellipse(0, 0, p.s, p.s * 0.6, 0, 0, Math.PI * 2); ctx.fill(); }
      else drawLeaf(p.s);
      ctx.restore();
    }
    raf = requestAnimationFrame(frame);
  }
  function start() {
    if (running) return;
    if (!canvas) makeCanvas();
    canvas.style.display = '';
    running = true; raf = requestAnimationFrame(frame);
  }
  function stop() {
    running = false; if (raf) cancelAnimationFrame(raf);
    if (canvas) { ctx.clearRect(0, 0, W, H); canvas.style.display = 'none'; }
  }
  document.addEventListener('visibilitychange', function () {
    if (!on) return;
    if (document.hidden) { running = false; if (raf) cancelAnimationFrame(raf); }
    else { running = true; raf = requestAnimationFrame(frame); }
  });

  function makeToggle() {
    var box = document.createElement('label');
    box.id = 'season-toggle';
    box.title = '계절 배경 효과 켜기/끄기';
    var cb = document.createElement('input'); cb.type = 'checkbox'; cb.checked = on;
    var span = document.createElement('span'); span.textContent = LABEL + ' 효과';
    box.appendChild(cb); box.appendChild(span);
    document.body.appendChild(box);
    cb.addEventListener('change', function () {
      on = cb.checked; setPref(on ? 'on' : 'off');
      if (on) start(); else stop();
    });
  }

  function init() { makeToggle(); if (on) start(); }
  if (document.body) init();
  else document.addEventListener('DOMContentLoaded', init);
})();
