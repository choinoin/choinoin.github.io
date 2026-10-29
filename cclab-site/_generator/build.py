#!/usr/bin/env python3
"""Generate the static CCLab@KNU site for GitHub Pages.

게시글은 content/ 폴더의 Markdown 파일에서 읽습니다.
  content/news/*.md             소식
  content/courses/<게시판>/*.md  강의자료
각 .md 파일 맨 위 front matter(--- 사이)에 title/date/file 을 적고, 그 아래에 본문을 씁니다.
새 글 = .md 파일 하나 추가 후 이 스크립트를 다시 실행.
"""
import html, json, os, re, sys

OUT = sys.argv[1]
CONTENT = os.path.join(OUT, "content")
# 사진·파일은 항상 사이트 내부(assets/)에서 불러온다 (www2 원격 의존 제거).
# 빌드할 때 환경변수가 없어도 로컬 자산을 쓰도록 기본값을 고정.
LOCAL = True
OLD = "ASSETROOT"
SCHOLAR = "https://scholar.google.com/citations?user=FQs_1FAAAAAJ&view_op=list_works&sortby=pubdate"
NAV = [("Home", ""), ("People", "people/"), ("Research", "research/"),
       ("Publications", "publications/"), ("News", "news/"), ("Courses", "courses/"),
       ("✎ 글쓰기", "write.html")]
e = html.escape

# 강의 게시판 표시 순서와 이름 (폴더명 = id)
COURSE_BOARDS = [
    ("일반화학및실험 1·2", "genchem"),
    ("자연과학의 이해", "natsci"),
    ("고등양자화학 1·2", "advquanchem"),
    ("통계역학", "statmech"),
    ("화학을위한수학 (전산화학)", "compchem"),
    ("물리화학 1·2", "physchem"),
    ("양자화학", "quanchem"),
    ("계산화학과분자모델링 (컴퓨터와화학)", "compandchem"),
    ("화학반응속도론", "chemkinetics"),
    ("구 강의게시판 (2007–2014, 통합 게시판)", "hhwang"),
]


def parse_md(path):
    """front matter(---) + 본문 파싱 → (meta dict, body str)."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    meta, body = {}, raw
    if raw.lstrip().startswith("---"):
        rest = raw.lstrip()[3:]
        fm, _sep, body = rest.partition("\n---")
        for line in fm.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = body.lstrip("\n")
    return meta, body.strip()


def _inline(s):
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    # 이미지 ![alt](src) — 링크보다 먼저 처리
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" class="post-img" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(((?:https?://|assets/)[^\s)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"(?<![\">=])(https?://[^\s<]+)",
               r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_html(text):
    """아주 작은 Markdown → HTML (제목·목록·굵게·링크·문단)."""
    lines = text.split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para[:] = []

    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            flush()
        elif ln.lstrip().startswith("#"):
            flush()
            h = ln.lstrip()
            lvl = min(len(h) - len(h.lstrip("#")), 4) + 2
            out.append("<h%d>%s</h%d>" % (lvl, _inline(h.lstrip("#").strip()), lvl))
        elif ln.lstrip()[:2] in ("- ", "* "):
            flush()
            items = []
            while i < len(lines) and lines[i].lstrip()[:2] in ("- ", "* "):
                items.append("<li>" + _inline(lines[i].lstrip()[2:].strip()) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        else:
            para.append(ln)
        i += 1
    flush()
    return "\n".join(out)


MODAL_HTML = """
<div id="pdfModal" class="modal" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="modal-head">
      <div><h3 id="modalTitle"></h3><time id="modalDate"></time></div>
      <button class="modal-x" data-close aria-label="닫기">×</button>
    </div>
    <div id="modalBody" class="modal-body"></div>
  </div>
</div>
"""

MODAL_JS = """
<script>
(function () {
  var root = '../';
  var modal = document.getElementById('pdfModal');
  if (!modal) return;
  var mTitle = document.getElementById('modalTitle'), mDate = document.getElementById('modalDate'), mBody = document.getElementById('modalBody');
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function open(file, title, date, body) {
    mTitle.textContent = title; mDate.textContent = date;
    modal.classList.toggle('has-pdf', !!(file && /\\.pdf$/i.test(file)));
    var top = body ? '<div class="modal-text">' + body.replace(/(src|href)=(["'])assets\\//g, '$1=$2' + root + 'assets/') + '</div>' : '';
    function fileHtml() {
      if (!file) return body ? '' : '<p class="modal-note">첨부 자료가 이 아카이브에 포함되어 있지 않습니다.</p>';
      var url = root + file, ext = (file.split('.').pop() || '').toLowerCase();
      if (ext === 'pdf') {
        return '<iframe src="' + url + '" title="' + esc(title) + '"></iframe>'
          + '<p class="modal-foot"><a href="' + url + '" target="_blank" rel="noopener">새 탭에서 열기</a> · <a href="' + url + '" download>내려받기</a></p>';
      }
      return '<p class="modal-foot"><a href="' + url + '" download>첨부파일 내려받기 (' + ext + ')</a></p>';
    }
    modal.hidden = false; document.body.style.overflow = 'hidden';
    if (file && window.cclabAsk && !window.cclabUnlocked()) {
      mBody.innerHTML = top + '<p class="modal-note">자료를 보려면 강의에서 안내한 코드를 입력하세요.</p>';
      window.cclabAsk(function () { mBody.innerHTML = top + fileHtml(); });
    } else {
      mBody.innerHTML = top + fileHtml();
    }
  }
  function close() { modal.hidden = true; mBody.innerHTML = ''; document.body.style.overflow = ''; }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('.arch-link');
    if (b) { ev.preventDefault(); open(b.dataset.file, b.dataset.title, b.dataset.date, b.dataset.body); return; }
    if (ev.target.closest('[data-close]')) close();
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && !modal.hidden) close(); });
})();
</script>"""


def load_posts(folder, render=True):
    """폴더의 *.md 를 읽어 날짜 내림차순 리스트로. 각 항목: dict(meta..., body)."""
    d = os.path.join(CONTENT, folder)
    posts = []
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            meta, body = parse_md(os.path.join(d, fn))
            item = dict(meta)
            item["title"] = meta.get("title", fn[:-3])
            item["date"] = meta.get("date", "")
            item["file"] = meta.get("file") or None
            item["body"] = (md_html(body) if render else body) if body else ""
            item["_fn"] = fn
            posts.append(item)
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    return posts


def img(src, alt, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<img src="{src}" alt="{e(alt)}" loading="lazy"{c} '
            f'onerror="this.closest(\'figure\') ? this.closest(\'figure\').remove() : this.remove()">')


def page(path, title, active, body, extra_head="", script=""):
    depth = path.count("/")
    root = "../" * depth
    _nav = []
    for t, u in NAV:
        cls = ' class="active"' if t == active else ''
        _nav.append('<a href="%s%s"%s>%s</a>' % (root, u, cls, t))
    nav = "".join(_nav)
    doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="강원대학교 화학과 전산화학연구실 (Computational Chemistry Lab, Kangwon National University)">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">{extra_head}
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}"><b>CCLab<span>@</span>KNU</b><small>강원대학교 화학과 전산화학연구실</small></a>
    <button class="nav-toggle" aria-label="메뉴 열기" aria-expanded="false" aria-controls="nav"><span></span><span></span><span></span></button>
    <nav class="nav" id="nav">{nav}</nav>
  </div>
</header>
<main><div class="wrap">
{body}
</div></main>
<footer class="site-footer">
  <div class="wrap">
    <span>© Computational Chemistry Lab, Department of Chemistry, Kangwon National University</span>
    <span>Maintained by Hyonseok Hwang</span>
  </div>
</footer>
<script>(function(){{var t=document.querySelector('.nav-toggle'),n=document.getElementById('nav');if(!t||!n)return;t.addEventListener('click',function(){{var o=n.classList.toggle('open');t.setAttribute('aria-expanded',o?'true':'false');}});n.addEventListener('click',function(e){{if(e.target.closest('a')){{n.classList.remove('open');t.setAttribute('aria-expanded','false');}}}});}})();</script>
<script src="{root}assets/gate.js" defer></script>
<script src="{root}assets/seasons.js" defer></script>{script}
</body>
</html>
"""
    if LOCAL:
        doc = doc.replace("ASSETROOT/", root + "assets/")
    full = os.path.join(OUT, path, "index.html") if path else os.path.join(OUT, "index.html")
    if path.endswith(".html"):
        full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(doc)


# ---------------------------------------------------------------- News
NEWS = load_posts("news")  # content/news/*.md


def news_items(items):
    return "\n".join(
        f'<li><time>{p["date"]}</time><span>{e(p["title"])}</span></li>' for p in items)


# ---------------------------------------------------------------- Home
home = f"""
<section class="hero">
  <div>
    <div class="eyebrow">Computational Chemistry Lab</div>
    <h1>계산과 이론으로<br>분자 세계의 메커니즘을 탐구합니다</h1>
    <p>강원대학교 화학과 전산화학연구실은 통계역학에 기반한 계산·이론 화학 방법과 컴퓨터 모의실험을 이용해, 세포막을 비롯한 다양한 계에서 일어나는 물리·화학적 과정의 메커니즘을 연구합니다.</p>
    <p><a href="research/">연구 분야 보기 →</a></p>
  </div>
  <figure>{img(OLD + "/images/cclab_20220414b.jpg", "CCLab 구성원 단체 사진")}</figure>
</section>

<div class="grid-2">
  <section class="card">
    <h2>Lab News</h2>
    <ul class="news-list">
{news_items(NEWS[:5])}
    </ul>
    <a class="more" href="news/">전체 소식 →</a>
  </section>
  <section class="card">
    <h2>Contact</h2>
    <dl class="contact">
      <dt>주소</dt><dd>(24341) 강원특별자치도 춘천시 강원대학길 1<br>강원대학교 자연과학대학 화학과</dd>
      <dt>교수연구실</dt><dd>자연대1호관 309호</dd>
      <dt>학생연구실</dt><dd>자연대1호관 308호</dd>
      <dt>TEL</dt><dd>+82-33-250-8497 (교수연구실)</dd>
      <dt>FAX</dt><dd>+82-33-259-5667 (과사무실)</dd>
      <dt>Email</dt><dd><a href="mailto:hhwang@kangwon.ac.kr">hhwang@kangwon.ac.kr</a></dd>
    </dl>
    <h3>Mailing Address</h3>
    <p style="margin:0;color:var(--muted)">Department of Chemistry, Kangwon National University<br>1 Kangwondaehak-gil, Chuncheon, Gangwon-do 24341, Republic of Korea</p>
  </section>
</div>
"""
page("", "CCLab@KNU · 강원대학교 전산화학연구실", "Home", home)

# ---------------------------------------------------------------- People
def read_one(relpath):
    p = os.path.join(CONTENT, relpath)
    return parse_md(p) if os.path.exists(p) else ({}, "")


def avatar(name, photo):
    if photo:
        return f'<div class="avatar">{img(OLD + "/" + photo, name)}</div>'
    initial = e(name[:1]) if name else "·"
    return f'<div class="avatar avatar-ph">{initial}</div>'


# PI
pi_meta, pi_body = read_one("people/pi.md")
pi_name = pi_meta.get("name", "")
pi_contacts = []
if pi_meta.get("email"):
    pi_contacts.append(f'<a href="mailto:{pi_meta["email"]}">{e(pi_meta["email"])}</a>')
if pi_meta.get("phone"):
    pi_contacts.append(e(pi_meta["phone"]))
pi_contact = " · ".join(pi_contacts)
pi_photo = pi_meta.get("photo", "")
pi_media = img(OLD + "/" + pi_photo, pi_name, "pi-photo") if pi_photo else avatar(pi_name, "")
pi_card = f"""
<div class="pi">
  {pi_media}
  <div>
    <h3>{e(pi_name)} <span class="pi-en">{e(pi_meta.get("name_en", ""))}</span></h3>
    <p class="role">{e(pi_meta.get("role", ""))}, 강원대학교 화학과{(" · " + pi_contact) if pi_contact else ""}</p>
    <div class="pi-bio">{md_html(pi_body)}</div>
  </div>
</div>
""" if pi_name else ""

# Members
GROUPS = [("resprof", "Research Professor"), ("postdoc", "Postdoctoral Fellows"), ("grad", "Graduate Students"),
          ("undergrad", "Undergraduate Students"), ("etc", "Members")]
_members = load_posts("people/members", render=False)
by_group = {}
for m in _members:
    by_group.setdefault(m.get("group", "etc"), []).append(m)
for g in by_group:
    by_group[g].sort(key=lambda m: int(m.get("order") or 0) if str(m.get("order") or "0").isdigit() else 0)

members_html = ""
for gid, gname in GROUPS:
    ppl = by_group.get(gid)
    if not ppl:
        continue
    cards = ""
    for m in ppl:
        meta_bits = []
        if m.get("research"):
            meta_bits.append(f'<span class="m-research">{e(m["research"])}</span>')
        if m.get("email"):
            meta_bits.append(f'<a class="m-mail" href="mailto:{m["email"]}">{e(m["email"])}</a>')
        extra = ("<div class=\"m-extra\">" + "".join(meta_bits) + "</div>") if meta_bits else ""
        cards += (f'<div class="member">{avatar(m["name"], m.get("photo", ""))}'
                  f'<div class="m-info"><b>{e(m["name"])}</b><small>{e(m.get("role", ""))}</small>{extra}</div></div>\n')
    members_html += f'<h3 class="grp">{gname}</h3>\n<div class="members">{cards}</div>\n'

# Alumni
_, alumni_body = read_one("people/alumni.md")
alumni_cards = ""
for line in alumni_body.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    n, _, d = line.partition("|")
    alumni_cards += f'<div class="alum"><b>{e(n.strip())}</b><small>{e(d.strip())}</small></div>\n'

# Gallery
_, gallery_body = read_one("people/gallery.md")
gallery = ""
for line in gallery_body.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = [x.strip() for x in line.split("|")]
    f = parts[0]
    d = parts[1] if len(parts) > 1 else ""
    c = parts[2] if len(parts) > 2 else ""
    gallery += (f'<figure>{img(OLD + "/" + f, c)}'
                f'<figcaption><b>{e(d)}</b>{e(c)}</figcaption></figure>\n')

people = f"""
<h1 class="page-title">People</h1>
<p class="page-lead">전산화학연구실 구성원</p>

<h2>Principal Investigator</h2>
{pi_card}

<h2>Members</h2>
{members_html}

<h2>Alumni</h2>
<div class="alumni">
{alumni_cards}
</div>

<h2>Photos</h2>
<div class="gallery">
{gallery}
</div>
"""
page("people/", "People · CCLab@KNU", "People", people)

# ---------------------------------------------------------------- Research
def fig(src, cap):
    c = f"<figcaption>{cap}</figcaption>" if cap else ""
    return f"<figure>{img(OLD + '/images/' + src, cap or src)}{c}</figure>"


research = f"""
<h1 class="page-title">Research</h1>
<p class="page-lead">계산 및 이론 화학으로 복잡한 분자계의 물리·화학적 과정을 연구합니다</p>

<div class="lang-toggle" role="group" aria-label="언어 선택">
  <button type="button" data-set="ko" class="on">한국어</button>
  <button type="button" data-set="en">English</button>
</div>

<div id="research" data-lang="ko">
<section class="topic">
  <p class="ko">전산화학연구실(이하 ‘우리 연구실’)에서는 <b>계산 및 이론 화학 방법</b>들을 이용하여 생체계 등 <b>다양한 계에서 일어나는 물리, 화학적 과정들의 메커니즘</b>에 대한 연구를 진행하고 있습니다. 우리 연구실에서 사용하는 계산 및 이론 화학 방법들은 <b>통계역학</b>에 기반을 두고 있으며, <b>컴퓨터를 이용한 모의실험(computer simulation)</b>이 주된 연구 방법의 하나입니다.</p>
  <p class="en">Our group studies physical and chemical processes in complex molecular systems such as cell membranes. We develop and apply computational and theoretical methods, mainly computer simulations based on classical and quantum statistical mechanics, to describe these processes at the atomic and molecular levels.</p>
</section>

<section class="topic">
  <h2><span class="ko">세포막에서 cyclic peptide nanotube의 구조와 기능</span><span class="en">Cyclic peptide nanotubes in cell membranes</span></h2>
  <p class="ko">이온채널은 세포막에 존재하는 막단백질의 한 종류로, 이온들의 세포막 통과에 관여하면서 신경과 근육의 자극, 감각신호 전달에 중요한 역할을 담당합니다. 미국 Scripps 연구소의 Ghadiri 교수 연구진이 합성한 cyclic peptide nanotube는 이온채널과 같은 기능을 하는 합성 단백질로, 항생제나 이온센서로 사용될 수 있다고 알려져 있습니다. cyclic peptide nanotube는 곁사슬(side chain)이 친수성인지 소수성인지에 따라 크게 두 종류로 나눌 수 있습니다.</p>
  <p class="en">Cyclic peptide nanotubes, synthesized by Prof. Ghadiri's group at the Scripps Research Institute, are synthetic proteins that function like ion channels and may be used as antibiotics or ion sensors. They fall into two classes depending on whether their side chains are hydrophilic or hydrophobic.</p>
  {fig("nanotube_types01.jpg", "")}
  <p class="ko">우리 연구실에서는 분자동역학 모의실험(molecular dynamics simulation)과 몬테카를로 모의실험(Monte Carlo simulation) 등을 이용하여 cyclic peptide nanotube가 선택적으로 양이온만을 통과시키는 원인과, nanotube와 세포막의 상호작용이 이온 이동에 미치는 영향 등을 연구하고 있습니다.</p>
  <p class="en">Using molecular dynamics (MD), Monte Carlo (MC) simulations and mean-field theories, we study why these nanotubes selectively transport cations and how nanotube–membrane interactions affect ion transport.</p>
  {fig("na_in_nanotube.png", "Hwang et al., <i>J. Phys. Chem. B</i> <b>110</b>, 26448 (2006)")}
</section>

<section class="topic">
  <h2><span class="ko">세포막에서 단백질 삽입과 결합</span><span class="en">Insertion and assembly of proteins into cell membranes</span></h2>
  <p class="ko">단백질 분자들이 세포막에 삽입되면서 서로 결합하는 메커니즘을 이해하는 것은 생물학 및 생명공학 분야에서 매우 중요합니다. 예를 들어 항균 펩타이드는 박테리아 세포막을 통과해 세포를 죽이는데, 이때 세포막과의 상호작용과 세포막 내 펩타이드 분자들 사이의 결합이 중요한 역할을 한다는 것은 밝혀졌지만 구체적인 메커니즘은 아직 알려져 있지 않습니다. 생물계의 큰 규모와 느린 반응속도 때문에 전원자 분자동역학 모의실험은 매우 긴 계산 시간이 필요합니다. 그 대안으로 여러 원자를 하나의 입자로 나타내는 coarse-grained 분자동역학 모의실험은 계산 효율을 크게 높일 수 있습니다. 우리 연구실에서는 이 방법을 이용하여 단백질이 세포막에 삽입되면서 서로 결합하는 메커니즘을 연구하고 있습니다.</p>
  <p class="en">We investigate how proteins such as antimicrobial peptides insert into and assemble within membranes. Because all-atom simulations of such large, slow processes are computationally expensive, we use coarse-grained (CG) MD simulations in which groups of atoms are represented as single beads.</p>
  {fig("cg_nanotube_insertion02.png", "")}
</section>

<section class="topic">
  <h2>DNA translocation</h2>
  <p class="ko">DNA translocation은 단일사슬 또는 이중사슬 DNA 분자가 세포막의 구멍(pore)이나 이온채널을 통해 세포막 한쪽에서 다른 쪽으로 이동하는 현상입니다. 이온 전류가 흐르는 이온채널에 DNA가 들어오면 전류가 감소하고, 그 감소 정도가 염기의 크기와 연관된다는 사실로부터 새로운 DNA 염기서열 분석 방법이 제안되었습니다. 우리 연구실에서는 Brownian 동역학 모의실험과 우리 연구실에서 개발한 kinetic lattice grand canonical Monte Carlo(KLGCMC) 모의실험을 결합하여, 세포막에 의한 반응장(reaction field)과 DNA 염기–이온 상호작용이 DNA translocation에 미치는 영향을 연구하고 있습니다.</p>
  <p class="en">DNA passing through an ion channel partially blocks the ion current, and the size of the drop depends on the bases — a basis for new DNA sequencing methods. We combine Brownian dynamics with our kinetic lattice grand canonical Monte Carlo (KLGCMC) method to study membrane reaction-field effects and DNA base–ion interactions during translocation.</p>
  {fig("dna_translocation02.png", "")}
</section>

<section class="topic">
  <h2><span class="ko">아르곤 기체에서 진행하는 충격파의 물리적 성질</span><span class="en">Shock waves in argon gas</span></h2>
  <p class="ko">충격파(shock wave)는 강렬한 폭발이나 초음속으로 움직이는 물체에 의해 발생하는 진행성 교란으로, 충격파 전선 전후에서 밀도·온도·압력 등이 급격히 변하는 것이 특징입니다. 우리 연구실에서는 아르곤 기체에서 충격파가 진행할 때 나타나는 아르곤 분자의 운동에너지 분포 등의 성질을 비평형 분자동역학 모의실험을 개발하여 연구하고 있습니다.</p>
  <p class="en">We study the physical properties of shock waves propagating in argon gas, such as the kinetic energy distribution of argon atoms, using nonequilibrium molecular dynamics (NEMD) simulations developed in our group.</p>
</section>
</div>
"""
research_js = """
<script>
(function () {
  var box = document.getElementById('research');
  var btns = document.querySelectorAll('.lang-toggle button');
  function set(l) {
    box.setAttribute('data-lang', l);
    btns.forEach(function (b) { b.classList.toggle('on', b.dataset.set === l); });
    try { localStorage.setItem('cclab-lang', l); } catch (e) {}
  }
  btns.forEach(function (b) { b.addEventListener('click', function () { set(b.dataset.set); }); });
  try { var s = localStorage.getItem('cclab-lang'); if (s) set(s); } catch (e) {}
})();
</script>"""
page("research/", "Research · CCLab@KNU", "Research", research, script=research_js)

# ---------------------------------------------------------------- Publications
# (year, authors, title, venue, note)
PUBS = [
    (2023, "H. J. Han, S. Y. Park, S. E. Jeon, J. S. Kwak, J. H. Lee, A. K. Jaladi, H. Hwang, and D. K. An", "Grignard Reagent-Catalyzed Hydroboration of Esters, Nitriles, and Imines", "Molecules <b>28</b>, 7090 (2023)", ""),
    (2023, "N. Kim, J. H. Lee, Y. Song, JH. Lee, G. C. Schatz, and H. Hwang", "Molecular Dynamics Simulation Study of the Protonation State Dependence of Glutamic Acid Transport through a Cyclic Peptide Nanotube", "J. Phys. Chem. B <b>127</b>, 6061 (2023)", ""),
    (2023, "S. Samala, J. H. Lee, Y. Park, S. J. Hong, H. Jo, H. Hwang, Y. M. Jung, K. M. Ok, J. Sessler, and C. H. Lee", "One Carbon Ring Expansion of Bipyrrole to Bipyridine Enables Access to a π-Extended, Non-innocent, Corrole-like Ligand", "Chem. Eur. J. (ASAP)", ""),
    (2022, "J. E. Seok, H. T. Kim, J. Kim, J. H. Lee, A. K. Jaladi, H. Hwang, and D. K. An", "Effective Magnesium-catalyzed Hydroboration of Nitriles and Imines", "Asian J. Org. Chem. <b>11</b>, e202200405 (2022)", ""),
    (2022, "H. Mubarok, S. W. Kwak, J. H. Lee, H. Hwang, K. M. Lee, Y. Kim, M. H. Lee, and M. H. Park", "Effect of bridging units on the photophysical properties of 4-NEt<sub>2</sub>-appended salen-indium complexes", "Bull. Korean Chem. Soc. <b>43</b>, 1177 (2022)", ""),
    (2022, "J. Kang, R. Zaen, J. H. Lee, H. Hwang, K. M. Park, S. C. Kim, J. Y. Lee, and Y. Kang", "Effect of Ancillary Ligand on the Photoluminescent and Electroluminescent Properties of Blue Ir(III) Complexes Bearing Main Bipyridine Ligand", "Chem. Eng. J. <b>431</b>, 134249 (2022)", ""),
    (2022, "I. Choi, N. Kim, Y. Song, G. C. Schatz, and H. Hwang", "Extended Kinetic Lattice Grand Canonical Monte Carlo Simulation Method for Transport of Multicomponent Ion Mixtures Through a Model Nanopore System", "Bull. Korean Chem. Soc. <b>43</b>, 343 (2022)", "Special issue"),
    (2022, "S. K. Kwak, H. Mubarok, J. H. Lee, H. Hwang, K. M. Lee, M. H. Lee, and M. H. Park", "Highly Red-emissive Salen-indium complexes: Impact of 4-amino-substitution on the photophysical properties", "Inorg. Chem. Front. <b>9</b>, 119 (2022)", ""),
    (2021, "C. H. Ryu, J. Lim, M. B. Kim, J. H. Lee, H. Hwang, J. Y. Lee, and K. M. Lee", "Tris(5-phenyl-1<i>H</i>-1,2,4-triazolyl)iridium(III) Complex and Its Use in Blue Phosphorescent Organic Light-Emitting Diodes to Provide an External Quantum Efficiency of up to 27.8%", "Adv. Optical Mater. <b>9</b>, 2001957 (2021)", ""),
    (2021, "S. H. Lee, M. S. Mun, J. H. Lee, S. Im, W. Lee, H. Hwang, and K. M. Lee", "Impact of the Electronic Environment in Carbazole-Appended <i>o</i>-Carboranyl Compounds on the Intramolecular-Charge-Transfer-Based Radiative Decay Efficiency", "Organometallics <b>40</b>, 959 (2021)", ""),
    (2021, "S. H. Lee†, J. H. Lee†, M. S. Mun, S. Yi, E. Yoo, H. Hwang, and K. M. Lee", "Influence of Electronic Environment on the Radiative Efficiency of 9-Phenyl-9<i>H</i>-carbazole-Based <i>ortho</i>-Carboranyl Luminophores", "Molecules <b>26</b>, 1763 (2021)", ""),
    (2021, "S. H. Lee, M. S. Mun, M. Kim, J. H. Lee, H. Hwang, W. Lee, and K. M. Lee", "Alteration of Intramolecular Electronic Transition via Deboronation of Carbazole-based <i>o</i>-carboranyl Compound and Intriguing ‘Turn-on’ emissive variation", "RSC Advances <b>11</b>, 24057 (2021)", ""),
    (2021, "J. Park†, J. H. Lee†, B. Lim, N. K. Lee, G. Sim, S. Ryu, I. Kim, H. Hwang, and J. Lee", "Fine Tuning of HOMO-LUMO gap of 6-(Thiophen-2-yl) indolizino[3,2-c]quinolines and the Self-Assembly Properties as FONs: Rational Design and Theoretical Calculation", "ChemPhotoChem <b>5</b>, 58 (2021)", ""),
    (2020, "J. H. Hong, S. Kim, H. So, J. H. Lee, H. Hwang, and K. M. Lee", "Intriguing ‘Turn-on’ Phosphorescent response in the Near Infrared Region upon Fluoride Binding: Dipyrromethene Chelating-based Triarylboryl-Iridium(III) Conjugates", "Dyes and Pigments <b>183</b>, 108706 (2020)", ""),
    (2020, "H. Kim, H. L. Shin, J. Yi, H. S. Choi, J. H. Lee, H. Hwang, and D. K. An", "Lithium Bromide/HBpin: A Mild and Effective Catalytic System for the Selective Hydroboration of Aldehydes and Ketones", "Bull. Korean Chem. Soc. <b>41</b>, 1009 (2020)", ""),
    (2020, "M. S. Mun, C. H. Ryu, M. Kim, J. H. Lee, H. Hwang, and K. M. Lee", "Multiple Photoluminescence of Spiro[acridine-fluorene]-Based <i>o</i>-carboranyl Compounds with Potential as a Visual Sensory Material", "J. Mater. Chem. C <b>8</b>, 16894 (2020)", ""),
    (2020, "H. Kim, H. T. Kim, J. H. Lee, H. Hwang, and D. K. An", "Lithium Bromide: An Inexpensive and Efficient Catalyst for Imine Hydroboration with Pinacolborane at room temperature", "RSC Advances <b>10</b>, 34421 (2020)", ""),
    (2020, "M. Kim, C. H. Ryu, J. H. Hong, J. H. Lee, H. Hwang, and K. M. Lee", "Planarity of N-aryl in Appended 1,2,4-triazole-based <i>o</i>-carboranyl Luminophores: A Key Factor to Control Intramolecular Charge Transfer", "Inorg. Chem. Front. <b>7</b>, 4180 (2020)", ""),
    (2020, "Y. Song, J. H. Lee, I. Jung, B. Seo, and H. Hwang", "Molecular Dynamics Simulations of Micelle Properties and Behaviors of Sodium Lauryl Ether Sulfate Penetrating Ceramide and Phospholipid Bilayers", "J. Phys. Chem. B <b>124</b>, 5919 (2020)", "Peter J. Rossky Festschrift"),
    (2020, "J. Park†, B. Lim†, N. K. Lee, J. H. Lee, K. Jang, S. W. Kang, I. Kim, H. Hwang, and J. Lee", "Dual-functioning IQ-LVs as Lysosomal Viscosity Probes with Red-shifted Emission and Inhibitors of Autophagic Flux", "Sens. Actuators B Chem. <b>309</b>, 127764 (2020)", ""),
    (2020, "S. Kim†, J. H. Lee†, H. So, J. Ryu, J. Lee, H. Hwang, Y. Kim, K. M. Lee, and M. H. Park", "Spirobifluorene-based <i>o</i>-Carboranyl Compounds: Insights into the Rotational Effect of Carborane Cages on Photoluminescence", "Chem. Eur. J. <b>26</b>, 548 (2020)", ""),
    (2020, "S. Kim, J. H. Lee, H. So, M. Kim, M. S. Mun, H. Hwang, M. H. Park, and K. M. Lee", "Insights into the Effects of Substitution Position on the Photophysics of Mono-<i>o</i>-Carborane-Substituted Pyrenes", "Inorg. Chem. Front. <b>7</b>, 2949 (2020)", ""),
    (2020, "H. Kim, J. H. Lee, H. Hwang, and D. K. An", "Quantitative NaH Catalytic Hydroboration of Aldimines", "New J. Chem. <b>44</b>, 11330 (2020)", ""),
    (2020, "H. So, M. S. Mun, M. Kim, J. H. Kim, J. H. Lee, H. Hwang, D. K. An, and K. M. Lee", "Deboronation-Induced Ratiometric Emission Variations of Terphenyl-Based <i>Closo</i>-<i>o</i>-Carboranyl Compounds: Applications to Fluoride-Sensing", "Molecules <b>25</b>, 2413 (2020)", ""),
    (2019, "B. Lim†, B. Baek†, K. Jang, N. K. Lee, J. H. Lee, Y. Lee, J. Kim, S. W. Kang, J. Park, S. Kim, N. W. Kang, S. Hong, D. D. Kim, I. Kim, H. Hwang, and J. Lee", "Novel turn-on fluorescent biosensors for selective detection of cellular Fe<sup>3+</sup> in lysosomes: Thiophene as a selectivity-tuning handle for Fe<sup>3+</sup> sensors", "Dyes and Pigments <b>169</b>, 51 (2019)", ""),
    (2019, "D. H. Ma, A. K. Jaladi, J. H. Lee, T. S. Kim, W. S. Shin, H. Hwang, and D. K. An", "Catalytic Hydroboration of Aldehydes, Ketones, and Alkenes Using Potassium Carbonate: A Small Key to Big Transformation", "ACS Omega <b>4</b>, 15893 (2019)", ""),
    (2019, "C. H. Ryu, S. W. Kwak, H. W. Lee, J. H. Lee, H. Hwang, M. Kim, Y. Chung, Y. Kim, M. H. Park, and K. M. Lee", "Carbazole-Appended Salen-Indium Conjugate System: Synthesis and Enhanced Luminescence Efficiency", "Inorg. Chem. <b>58</b>, 12358 (2019)", ""),
    (2019, "J. Y. Lee, J. Kim, J. H. Lee, H. Hwang, and E. J. Yoo", "Higher-order Cycloaddition of N-Aromatic Zwitterions and Ketenes to Access Diazepine Derivatives", "Asian J. Org. Chem. <b>8</b>, 1654 (2019)", ""),
    (2019, "S. W. Kwak, M. B. Kim, H. Shin, J. H. Lee, H. Hwang, J. Y. Ryu, J. Lee, M. Kim, Y. Chung, J. C. Choe, Y. Kim, K. M. Lee, and M. H. Park", "A Series of Quinolinol-Based Indium Luminophores: A Rotational Design Approach for Manipulating Photophysical Properties", "Inorg. Chem. <b>58</b>, 8056 (2019)", ""),
    (2019, "S. W. Kwak†, H. Jin†, J. H. Lee, H. Hwang, M. Kim, Y. Kim, Y. Chung, K. M. Lee, and M. H. Park", "Systematic control of the overlapping energy region for an efficient intramolecular energy transfer: Functionalized salen-Al/triphenylamine guest-host assemblies", "Inorg. Chem. <b>58</b>, 2454 (2019)", ""),
    (2019, "Y. Baek†, Y. Kwon†, C. Maeng, J. H. Lee, H. Hwang, K. M. Lee, and P. H. Lee", "Pyrazinoindole-based Lewis acid/base assembly: Intriguing intramolecular charge-transfer switching through the dual-sensing of fluoride and acid", "J. Org. Chem. (2019)", ""),
    (2019, "H. So, J. Kim, J. H. Lee, H. Hwang, H. Kwon, D. K. An, and K. M. Lee", "Planarity of Terphenyl Rings Possessing <i>o</i>-Carborane Cages: Turning on Intramolecular-Charge-Transfer-Based Emission", "Chem. Commun. <b>55</b>, 14518 (2019)", ""),
    (2019, "S. Kim, H. So, J. H. Lee, H. Hwang, H. Kwon, M. H. Park, and K. M. Lee", "Photophysical Properties of Spirobifluorene-based <i>o</i>-Carboranyl Compounds Altered by Structurally Rotating the Carborane Cages", "Molecules <b>24</b>, 4135 (2019)", ""),
    (2019, "A. K. Jaladi, H. Kim, J. H. Lee, W. K. Shin, H. Hwang, and D. K. An", "Lithium diisobutyl-tert-butoxyaluminum hydride (LDBBA) catalyzed hydroboration of alkynes and imines with pinacolborane", "New J. Chem. <b>43</b>, 16524 (2019)", ""),
    (2019, "H. Jin†, S. Kim†, H. J. Bae, J. H. Lee, H. Hwang, M. H. Park, and K. M. Lee", "Effect of planarity of aromatic rings appended to <i>o</i>-carborane on photophysical properties: A series of <i>o</i>-carboranyl compounds based on 2-phenylpyridine- and 2-(benzo[<i>b</i>]thiophen-2-yl)pyridine", "Molecules <b>24</b>, 201 (2019)", ""),
    (2019, "H. Jin, H. J. Bae, S. Kim, J. H. Lee, H. Hwang, M. H. Park, and K. M. Lee", "2-Phenylpyridine- and 2-(benzo[<i>b</i>]thiophen-2-yl)pyridine-based <i>o</i>-carboranyl compounds: Impact of the structural formation of aromatic rings on photophysical properties", "Dalton Trans. <b>48</b>, 1467 (2019)", ""),
    (2018, "J. H. Lee†, C. H. Lee†, S. Yu, H. Hwang, and K. M. Lee", "Quinolinol-based Al/triarylborane dyad assembly: Alternation of electronic transition states mediated by fluoride anion binding", "Bull. Korean Chem. Soc. <b>39</b>, 1294 (2018)", ""),
    (2018, "Y. Seo†, Y. Song†, G. C. Schatz, and H. Hwang", "Conformational effects in the transport of glucose through a cyclic peptide nanotube: A molecular dynamics simulation study", "J. Phys. Chem. B <b>122</b>, 8174 (2018)", ""),
    (2018, "K. Hyun†, H. Jin†, W. H. Woo†, J. H. Lee, H. Hwang, M. Kim, K. M. Lee, M. H. Park, and Y. Kim", "Systematic design of indium-based luminophores with color-tunable emission via combined manipulation of HOMO and LUMO levels", "Dyes and Pigments <b>158</b>, 285 (2018)", ""),
    (2018, "S. W. Kwak, H. Jin, H. Shin, J. H. Lee, H. Hwang, J. Lee, M. Kim, Y. Chung, Y. Kim, K. M. Lee, and M. H. Park", "A salen-Al/carbazole dyad-based guest-host assembly: Enhancement of luminescence efficiency via intramolecular energy transfer", "Chem. Commun. <b>54</b>, 4712 (2018)", ""),
    (2018, "S. W. Kwak†, H. Kwon†, J. H. Lee, H. Hwang, M. Kim, Y. Chung, Y. Kim, K. M. Lee, and M. H. Park", "Salen-indium/triarylborane triads: Synthesis and ratiometric emission-colour changes by fluoride ion binding", "Dalton Trans. <b>47</b>, 5310 (2018)", ""),
    (2017, "D. K. You, J. H. Lee, H. Hwang, H. Kwon, M. H. Park, and K. M. Lee", "Deboronation-induced ratiometric emission sensing of fluoride by 1,3,5-tris-(<i>o</i>-carboranyl-methyl)benzene", "Tetrahedron Lett. <b>58</b>, 3246 (2017)", ""),
    (2017, "S. W. Kwak, B. H. Choi, J. H. Lee, H. Hwang, J. Lee, H. Kwon, Y. Chung, K. M. Lee, and M. H. Park", "Synthesis and dual-emission feature of salen-Al/triarylborane dyads", "Inorg. Chem. <b>56</b>, 6039 (2017)", ""),
    (2017, "N. Shin, S. Yu, J. H. Lee, H. Hwang, and K. M. Lee", "Biphenyl- and fluorene-based <i>o</i>-carboranyl compounds: Alteration of photophysical properties by distortion of biphenyl rings", "Organometallics <b>36</b>, 1522 (2017)", ""),
    (2017, "D. K. You†, J. H. Lee†, B. H. Choi, H. Hwang, M. H. Lee, K. M. Lee, and M. H. Park", "Effects of Multi-carborane Substitution on the Photophysical and Electron Accepting Properties of <i>o</i>-carboranylbenzene Compounds", "Eur. J. Inorg. Chem. <b>2017</b>, 2496 (2017)", ""),
    (2017, "S. H. Lee, N. Shin, S. W. Kwak, K. Hyun, W. H. Woo, J. H. Lee, H. Hwang, M. Kim, J. Lee, Y. Kim, K. M. Lee, and M. H. Park", "Intriguing indium-salen complexes as multicolor luminophores", "Inorg. Chem. <b>56</b>, 2621 (2017)", ""),
    (2017, "D. K. You, S. H. Lee, J. H. Lee, S. W. Kwak, H. Hwang, J. Lee, Y. Chung, M. H. Park, and K. M. Lee", "Synthesis and photophysical properties of phenanthroimidazole-triarylborane dyads: intriguing ‘turn-on’ sensing mediated by fluoride anions", "RSC Adv. <b>7</b>, 10345 (2017)", ""),
    (2017, "Y. Seo†, Y. Song†, G. C. Schatz, and H. Hwang", "Energetic and Frictional Effects in the Transport of Ions in a Cyclic Peptide Nanotube", "Bull. Korean Chem. Soc. <b>38</b>, 19 (2017)", "Cover"),
    (2016, "Y. Song, J. H. Lee, H. Hwang, G. C. Schatz, and H. Hwang", "Energetic and Dynamic Analysis of Transport of Na<sup>+</sup> and K<sup>+</sup> through a Cyclic Peptide Nanotube in Water and in Lipid Bilayers", "J. Phys. Chem. B <b>120</b>, 11912 (2016)", ""),
    (2016, "J. H. Lee, H. Hwang, and K. M. Lee", "<i>p</i>-Terphenyl-based di-<i>o</i>-carboranyl compounds: Alteration of electronic transition state by terminal phenyl groups", "J. Organomet. Chem. <b>825</b>, 69 (2016)", ""),
    (2016, "A. Abebayehu, R. Dutta, S. J. Kim, J. H. Lee, H. Hwang, and C. H. Lee", "Synthesis and Multi-Oxo Anion-Binding Properties of Oligopyrrolic Macrocycles Based on Naphthobipyrrole", "Eur. J. Org. Chem. <b>2016</b>, 3959 (2016)", ""),
    (2016, "B. H. Choi, J. H. Lee, H. Hwang, K. M. Lee, and M. H. Park", "Novel Dimeric <i>o</i>-Carboranyl Triarylborane: Intriguing Ratiometric Color-Tunable Sensor via Aggregation-Induced Emission by Fluoride Anions", "Organometallics <b>35</b>, 1771 (2016)", ""),
]


def bold_pi(a):
    return a.replace("H. Hwang", "<b>H. Hwang</b>")


# Publications: content/publications/*.md (한 논문 = 파일 하나). 없으면 내장 목록(PUBS).
pub_posts = load_posts("publications", render=False)
pub_html = ""
if pub_posts:
    def _pubkey(p):
        try:
            y = int(p.get("year") or 0)
        except ValueError:
            y = 0
        try:
            # 번호 없는 새 글은 해당 연도 맨 위로
            num = int(p.get("num")) if str(p.get("num") or "").strip() else 10 ** 9
        except ValueError:
            num = 10 ** 9
        return (y, num)
    pub_posts.sort(key=_pubkey, reverse=True)
    cur = None
    for en in pub_posts:
        y = en.get("year") or "In press"
        if y != cur:
            if cur is not None:
                pub_html += "</ol>\n"
            pub_html += f'<h3 class="year" data-year="{y}">{y}</h3>\n<ol class="pubs">\n'
            cur = y
        pdf = ""
        f = en.get("pdf") or en.get("file")
        if f:
            fn = f.rsplit("/", 1)[-1]  # 파일명만 사용
            href = OLD + "/publications/papers/" + fn
            pdf = f' <a class="pdf-link" href="{href}" target="_blank" rel="noopener">PDF</a>'
        pub_html += f'<li data-n="{en.get("num", "")}">{bold_pi(en["body"])}{pdf}</li>\n'
    pub_html += "</ol>\n"
else:
    n = len(PUBS)
    cur = None
    for i, (y, a, t, v, note) in enumerate(PUBS):
        if y != cur:
            if cur is not None:
                pub_html += "</ol>\n"
            pub_html += f'<h3 class="year" data-year="{y}">{y}</h3>\n<ol class="pubs">\n'
            cur = y
        tag = f'<span class="tag">{note}</span>' if note else ""
        pub_html += (f'<li data-n="{n - i}"><div>{bold_pi(a)},</div>'
                     f'<div class="pub-title">“{t}”{tag}</div>'
                     f'<div class="pub-meta">{v}</div></li>\n')
    pub_html += "</ol>\n"

pubs = f"""
<h1 class="page-title">Publications</h1>
<p class="page-lead">† Equal contribution · 전체 목록은 <a href="{SCHOLAR}" target="_blank" rel="noopener">Google Scholar</a>에서 확인할 수 있습니다.</p>

<p class="note">제목 옆 <b>PDF</b> 링크로 논문 원문을 받을 수 있습니다.</p>

<div class="pub-tools">
  <input type="search" id="q" placeholder="저자, 제목, 저널로 검색" aria-label="논문 검색">
  <span id="count" style="color:var(--muted);font-size:.9rem"></span>
</div>
{pub_html}
"""
pubs_js = """
<script>
(function () {
  var q = document.getElementById('q'), count = document.getElementById('count');
  var items = Array.prototype.slice.call(document.querySelectorAll('ol.pubs li'));
  function run() {
    var s = q.value.trim().toLowerCase(), shown = 0;
    items.forEach(function (li) {
      var ok = !s || li.textContent.toLowerCase().indexOf(s) > -1;
      li.style.display = ok ? '' : 'none'; if (ok) shown++;
    });
    document.querySelectorAll('ol.pubs').forEach(function (ol) {
      var any = Array.prototype.some.call(ol.children, function (li) { return li.style.display !== 'none'; });
      ol.style.display = any ? '' : 'none';
      ol.previousElementSibling.style.display = any ? '' : 'none';
    });
    count.textContent = shown + '편';
  }
  q.addEventListener('input', run); run();
})();
</script>"""
page("publications/", "Publications · CCLab@KNU", "Publications", pubs, script=pubs_js)

# ---------------------------------------------------------------- News
news_items_html = "".join(
    f'<li data-t="{e(p["title"])}"><time>{p["date"]}</time>'
    f'<button class="arch-link" data-file="" data-body="{e(p["body"])}" '
    f'data-title="{e(p["title"])}" data-date="{p["date"]}">{e(p["title"])}</button></li>'
    for p in NEWS)
news = f"""
<h1 class="page-title">Lab News</h1>
<p class="page-lead">연구실 소식 · 제목을 클릭하면 내용이 열립니다.</p>
<ul class="news-list arch">{news_items_html}</ul>
{MODAL_HTML}
"""
page("news/", "News · CCLab@KNU", "News", news, script=MODAL_JS)

# ---------------------------------------------------------------- Courses
courses = """
<h1 class="page-title">Courses</h1>
<p class="page-lead">황현석 교수 담당 강의</p>
<div class="course-grid">
  <section class="card">
    <h3>학부</h3>
    <ul>
      <li><b>1학년</b> · 일반화학및실험 1, 2</li>
      <li><b>1학년</b> · 자연과학의 이해</li>
      <li><b>2학년</b> · 화학을위한수학</li>
      <li><b>2학년</b> · 물리화학 1, 2</li>
      <li><b>3학년</b> · 양자화학</li>
      <li><b>4학년</b> · 계산화학과분자모델링</li>
      <li><b>4학년</b> · 화학반응속도론</li>
    </ul>
  </section>
  <section class="card">
    <h3>대학원</h3>
    <ul>
      <li>고등양자화학 1, 2</li>
      <li>통계역학</li>
    </ul>
  </section>
</div>

<h2>강의자료 아카이브</h2>
<p class="note">강의자료 목록입니다. 제목을 클릭하면 본문과 첨부 PDF를 볼 수 있습니다. (일반화학·자연과학의이해는 원본 PDF가 서버에 남아 있지 않아 제목만 표시됩니다.)</p>

<div class="pub-tools">
  <input type="search" id="bq" placeholder="제목으로 검색" aria-label="강의자료 검색">
  <span id="bcount" style="color:var(--muted);font-size:.9rem"></span>
</div>

{boards_html}

<div id="pdfModal" class="modal" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="modal-head">
      <div><h3 id="modalTitle"></h3><time id="modalDate"></time></div>
      <button class="modal-x" data-close aria-label="닫기">×</button>
    </div>
    <div id="modalBody" class="modal-body"></div>
  </div>
</div>
"""


def board_block(name, rows, open_first=False):
    # rows: list of (date, title, file_or_None)
    if not rows:
        body = '<p style="color:var(--muted);padding:8px 0">등록된 글이 없습니다.</p>'
    else:
        items = []
        for row in rows:
            d, t, f = row[0], row[1], row[2]
            bodytext = row[3] if len(row) > 3 else ""
            if f or bodytext:
                items.append(
                    f'<li data-t="{e(t)}"><time>{d}</time>'
                    f'<button class="arch-link" data-file="{e(f or "")}" data-body="{e(bodytext or "")}" '
                    f'data-title="{e(t)}" data-date="{d}">{e(t)}</button></li>')
            else:
                items.append(f'<li data-t="{e(t)}"><time>{d}</time><span>{e(t)}</span></li>')
        body = f'<ul class="news-list arch">{chr(10).join(items)}</ul>'
    op = " open" if open_first else ""
    return (f'<details class="board"{op}><summary class="board-head">'
            f'<h2>{e(name)}</h2><span class="meta">{len(rows)}건</span></summary>'
            f'{body}</details>')


# 강의자료: content/courses/<게시판>/*.md 에서 읽는다
blocks = []
for name, bid in COURSE_BOARDS:
    posts = load_posts(os.path.join("courses", bid))
    rows = [(p["date"], p["title"], p["file"], p["body"]) for p in posts]
    blocks.append(board_block(name, rows))
boards_html = "\n".join(blocks)

courses = courses.format(boards_html=boards_html)
search_js = """
<script>
(function () {
  var q = document.getElementById('bq'), count = document.getElementById('bcount');
  if (!q) return;
  var items = Array.prototype.slice.call(document.querySelectorAll('ul.arch li'));
  function run() {
    var s = q.value.trim().toLowerCase(), shown = 0;
    items.forEach(function (li) {
      var ok = !s || (li.getAttribute('data-t') || '').toLowerCase().indexOf(s) > -1;
      li.style.display = ok ? '' : 'none'; if (ok) shown++;
    });
    document.querySelectorAll('details.board').forEach(function (d) {
      var any = Array.prototype.some.call(d.querySelectorAll('li'), function (li) { return li.style.display !== 'none'; });
      if (d.querySelector('ul.arch')) { d.style.display = any || !s ? '' : 'none'; if (s && any) d.open = true; }
    });
    count.textContent = s ? shown + '건' : '';
  }
  q.addEventListener('input', run);
})();
</script>"""
page("courses/", "Courses · CCLab@KNU", "Courses", courses, script=search_js + MODAL_JS)

# ---------------------------------------------------------------- Write (글쓰기)
board_js = "[" + ",".join("{id:%r,name:%r}" % (bid, name) for name, bid in COURSE_BOARDS) + "]"
write_body = """
<h1 class="page-title">글쓰기</h1>
<p class="page-lead">폼으로 글을 쓰고 아래 버튼을 누르면 <b>올바른 경로의 MD 파일과 첨부가 담긴 zip</b>이 내려받아집니다.
그 zip을 사이트 폴더(저장소) 루트에 풀어넣고 커밋(또는 다시 빌드)하면 글이 추가됩니다.</p>

<div class="wform">
  <label>구분
    <select id="w-section">
      <option value="news">News (소식)</option>
      <option value="course">Courses (강의자료)</option>
      <option value="pub">Publications (논문)</option>
    </select>
  </label>
  <label id="w-board-wrap">게시판
    <select id="w-board"></select>
  </label>
  <div id="w-title-wrap" class="w-row">
    <label>제목 <input type="text" id="w-title" placeholder="글 제목"></label>
    <label>날짜 <input type="text" id="w-date" placeholder="YYYY.MM.DD"></label>
  </div>
  <div id="w-pub-wrap">
    <label>연도 <input type="text" id="w-year" placeholder="2026"></label>
    <label>인용 정보 (저자, 제목, 저널 · &lt;i&gt; &lt;b&gt; 태그 사용 가능)
      <textarea id="w-cite" rows="3" placeholder='A. Author, ..., and H. Hwang, "Title", J. Name &lt;b&gt;12&lt;/b&gt;, 345 (2026).'></textarea>
    </label>
  </div>
  <label id="w-body-wrap">본문 (마크다운 · 비워도 됨)
    <textarea id="w-body" rows="8" placeholder="본문을 마크다운으로 작성"></textarea>
  </label>
  <label>첨부파일 <input type="file" id="w-files" multiple></label>
  <div class="wform-btns">
    <button type="button" id="w-render-btn" class="btn-ghost">실제 미리보기</button>
    <button type="button" id="w-preview-btn" class="btn-ghost">MD 미리보기</button>
    <button type="button" id="w-zip-btn" class="btn">zip 다운로드</button>
    <button type="button" id="w-fs-btn" class="btn-ghost" style="display:none">폴더에 바로 저장 (크롬)</button>
  </div>
  <pre id="w-preview" class="wform-preview" hidden></pre>
</div>
""" + MODAL_HTML
write_script = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script>
(function () {
  var BOARDS = __BOARDS__;
  var $ = function (id) { return document.getElementById(id); };
  var sec = $('w-section');
  function today() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + '.' + p(d.getMonth() + 1) + '.' + p(d.getDate()); }
  $('w-date').value = today();
  var bs = $('w-board');
  BOARDS.forEach(function (b) { var o = document.createElement('option'); o.value = b.id; o.textContent = b.name; bs.appendChild(o); });
  function sync() { var s = sec.value;
    $('w-board-wrap').style.display = s === 'course' ? '' : 'none';
    $('w-pub-wrap').style.display = s === 'pub' ? '' : 'none';
    $('w-title-wrap').style.display = s === 'pub' ? 'none' : '';
    $('w-body-wrap').style.display = s === 'pub' ? 'none' : '';
  }
  sec.addEventListener('change', sync); sync();

  function slug(s) { return (s || '').trim().replace(/[\\\\/:*?"<>|]+/g, '').replace(/\\s+/g, '-').slice(0, 40) || 'post'; }
  function san(n) { return n.replace(/[\\\\/:*?"<>|]+/g, '_').replace(/\\s+/g, '_'); }
  function fm(obj) { var l = ['---']; Object.keys(obj).forEach(function (k) { if (obj[k] !== '' && obj[k] != null) l.push(k + ': ' + obj[k]); }); l.push('---'); return l.join('\\n'); }

  function build() {
    var s = sec.value, files = $('w-files').files, items = [], mdPath, md;
    if (s === 'pub') {
      var year = $('w-year').value.trim(), cite = $('w-cite').value.trim();
      if (!cite) { alert('인용 정보를 입력하세요.'); return null; }
      var pdf = files.length ? san(files[0].name) : '';
      mdPath = 'content/publications/' + (year || 'new') + '-' + slug(cite.slice(0, 24)) + '.md';
      md = fm({ num: '', year: year, pdf: pdf }) + '\\n\\n' + cite + '\\n';
      if (files.length) items.push({ path: 'assets/publications/papers/' + pdf, file: files[0] });
    } else {
      var title = $('w-title').value.trim(), date = $('w-date').value.trim(), body = $('w-body').value;
      if (!title) { alert('제목을 입력하세요.'); return null; }
      var base = date.replace(/\\./g, '-') + '-' + slug(title);
      if (s === 'news') {
        mdPath = 'content/news/' + base + '.md';
        var extra = '';
        for (var i = 0; i < files.length; i++) { var nm = san(files[i].name); extra += '\\n\\n[첨부: ' + files[i].name + '](assets/uploads/' + nm + ')'; items.push({ path: 'assets/uploads/' + nm, file: files[i] }); }
        md = fm({ title: title, date: date }) + '\\n\\n' + body + extra + '\\n';
      } else {
        var board = $('w-board').value, fileRef = '';
        for (var j = 0; j < files.length; j++) { var nm2 = san(files[j].name); var pth = 'assets/boards/' + board + '/' + nm2; if (j === 0) fileRef = pth; items.push({ path: pth, file: files[j] }); }
        mdPath = 'content/courses/' + board + '/' + base + '.md';
        md = fm({ title: title, date: date, file: fileRef }) + '\\n\\n' + body + '\\n';
      }
    }
    items.unshift({ path: mdPath, text: md });
    return items;
  }

  $('w-preview-btn').addEventListener('click', function () {
    var items = build(); if (!items) return; var p = $('w-preview'); p.hidden = false;
    var list = items.map(function (it) { return (it.text ? '📄 ' : '📎 ') + it.path; }).join('\\n');
    p.textContent = '[생성될 파일]\\n' + list + '\\n\\n[MD 내용]\\n' + items[0].text;
  });

  // 실제 렌더 미리보기 (사이트와 동일하게)
  function mdInline(s) {
    s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    s = s.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>').replace(/`(.+?)`/g, '<code>$1</code>');
    s = s.replace(/!\\[([^\\]]*)\\]\\(([^)\\s]+)\\)/g, '<img src="$2" alt="$1" style="max-width:100%">');
    s = s.replace(/\\[([^\\]]+)\\]\\(((?:https?:\\/\\/|assets\\/)[^\\s)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return s;
  }
  function mdHtml(text) {
    var lines = (text || '').split('\\n'), out = [], para = [];
    function flush() { if (para.length) { out.push('<p>' + para.map(mdInline).join('<br>') + '</p>'); para = []; } }
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i].replace(/\\s+$/, '');
      if (!ln.trim()) flush();
      else if (/^\\s*#/.test(ln)) { flush(); var h = ln.replace(/^\\s+/, ''); var lvl = Math.min(h.match(/^#+/)[0].length, 4) + 2; out.push('<h' + lvl + '>' + mdInline(h.replace(/^#+\\s*/, '')) + '</h' + lvl + '>'); }
      else if (/^\\s*[-*]\\s/.test(ln)) { flush(); var it2 = []; while (i < lines.length && /^\\s*[-*]\\s/.test(lines[i])) { it2.push('<li>' + mdInline(lines[i].replace(/^\\s*[-*]\\s/, '')) + '</li>'); i++; } i--; out.push('<ul>' + it2.join('') + '</ul>'); }
      else para.push(ln);
    }
    flush(); return out.join('\\n');
  }
  var rm = document.getElementById('pdfModal'), rmT = document.getElementById('modalTitle'), rmD = document.getElementById('modalDate'), rmB = document.getElementById('modalBody'), objURLs = [];
  function closeR() { rm.hidden = true; rmB.innerHTML = ''; document.body.style.overflow = ''; objURLs.forEach(function (u) { URL.revokeObjectURL(u); }); objURLs = []; }
  rm.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) closeR(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !rm.hidden) closeR(); });
  $('w-render-btn').addEventListener('click', function () {
    var s = sec.value, files = $('w-files').files, title, date, bodyHtml = '';
    if (s === 'pub') { title = '(논문)'; date = $('w-year').value.trim(); var cite = $('w-cite').value.trim(); if (!cite) { alert('인용 정보를 입력하세요.'); return; } bodyHtml = cite; }
    else { title = $('w-title').value.trim(); date = $('w-date').value.trim(); if (!title) { alert('제목을 입력하세요.'); return; } bodyHtml = mdHtml($('w-body').value); }
    var fileHtml = '';
    if (files.length) {
      var f = files[0], url = URL.createObjectURL(f); objURLs.push(url);
      var ext = (f.name.split('.').pop() || '').toLowerCase();
      if (ext === 'pdf') fileHtml = '<iframe src="' + url + '" style="width:100%;height:60vh;border:0;background:#f4f2ee"></iframe>';
      else if (/^(jpg|jpeg|png|gif|webp)$/.test(ext)) fileHtml = '<img src="' + url + '" style="max-width:100%;display:block;margin:10px 0">';
      else fileHtml = '<p class="modal-foot">첨부: ' + f.name + '</p>';
    }
    rm.classList.toggle('has-pdf', !!(files.length && /\\.pdf$/i.test(files[0].name)));
    rmT.textContent = title; rmD.textContent = date;
    rmB.innerHTML = (bodyHtml ? '<div class="modal-text">' + bodyHtml + '</div>' : '') + fileHtml;
    rm.hidden = false; document.body.style.overflow = 'hidden';
  });

  $('w-zip-btn').addEventListener('click', function () {
    var items = build(); if (!items) return;
    if (typeof JSZip === 'undefined') { alert('JSZip 로딩 실패 — 인터넷 연결이 필요합니다.'); return; }
    var zip = new JSZip(), pending = [];
    items.forEach(function (it) { if (it.text != null) zip.file(it.path, it.text); else pending.push(it.file.arrayBuffer().then(function (buf) { zip.file(it.path, buf); })); });
    Promise.all(pending).then(function () { return zip.generateAsync({ type: 'blob' }); }).then(function (blob) {
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'cclab-post.zip'; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
  });

  var fsBtn = $('w-fs-btn');
  if (window.showDirectoryPicker) {
    fsBtn.style.display = '';
    fsBtn.addEventListener('click', function () {
      var items = build(); if (!items) return;
      window.showDirectoryPicker().then(function (root) {
        var chain = Promise.resolve();
        items.forEach(function (it) {
          chain = chain.then(function () {
            var parts = it.path.split('/'), dir = Promise.resolve(root);
            for (var k = 0; k < parts.length - 1; k++) (function (name) { dir = dir.then(function (d) { return d.getDirectoryHandle(name, { create: true }); }); })(parts[k]);
            return dir.then(function (d) { return d.getFileHandle(parts[parts.length - 1], { create: true }); })
              .then(function (fh) { return fh.createWritable(); })
              .then(function (w) { return (it.text != null ? Promise.resolve(it.text) : it.file.arrayBuffer()).then(function (data) { return w.write(data).then(function () { return w.close(); }); }); });
          });
        });
        return chain;
      }).then(function () { alert('저장 완료. 사이트를 다시 빌드하거나 커밋하세요.'); })
        .catch(function (e) { if (e.name !== 'AbortError') alert('저장 실패: ' + e.message); });
    });
  }
})();
</script>""".replace("__BOARDS__", board_js)
page("write.html", "글쓰기 · CCLab@KNU", "✎ 글쓰기", write_body, script=write_script)

# ---------------------------------------------------------------- 404
page("404.html", "Page not found · CCLab@KNU", "",
     '<h1 class="page-title">페이지를 찾을 수 없습니다</h1>'
     '<p class="page-lead">주소가 바뀌었거나 삭제된 페이지입니다. <a href="/">홈으로 이동</a></p>')

open(os.path.join(OUT, ".nojekyll"), "w").close()
print("pubs:", len(PUBS))
