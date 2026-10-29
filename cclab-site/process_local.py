#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCLab 로컬 빌더 — 받아둔 public_html 에서 완성 사이트를 만듭니다.

● 하는 일
  - 세팔보드(cgi-bin/spboard)의 게시글(제목·날짜·본문·첨부 PDF)을 읽어 사이트에 반영
  - 사진/연구 이미지/논문 PDF 를 사이트 안(assets/)으로 복사 → 서버 없이 자립
  - 비밀번호·회원정보·IP·관리자 설정 등 민감 파일은 전혀 포함하지 않음
  - News(소식)와 Courses(강의자료, PDF 모달) 생성

● 쓰는 법 (받아둔 public_html 이 있는 컴퓨터에서)
    python3 process_local.py /경로/public_html
  (출력 폴더를 지정하려면)  python3 process_local.py /경로/public_html ./cclab-site

표준 라이브러리만 사용합니다. 끝나면 cclab-site/ 를 GitHub Pages 저장소에 올리면 됩니다.
"""
import html, json, os, re, shutil, subprocess, sys

if len(sys.argv) < 2:
    sys.exit("사용법: python3 process_local.py <public_html 경로> [출력폴더]")
PUB = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else HERE
GEN = os.path.join(OUT, "_generator")
CONTENT = os.path.join(OUT, "content")
SP = os.path.join(PUB, "cgi-bin", "spboard")

if not os.path.isdir(SP):
    sys.exit("세팔보드 폴더를 찾지 못했습니다: " + SP)

# (표시 이름, 게시판 id)  — cclab 은 News 로 따로 처리
COURSES = [
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


def dec(b):
    for enc in ("cp949", "euc-kr", "utf-8"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("latin-1", "replace")


def read(path):
    with open(path, "rb") as f:
        return dec(f.read())


def fmt_date(s):
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", s or "")
    return "%s.%02d.%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else (s or "")


TAG = re.compile(r"<[^>]+>")


def body_of(bid, gul):
    """cmt_data/<gul>.cgi 의 본문 필드만 추출(비밀번호·IP·UA 제거)."""
    p = os.path.join(SP, "id", bid, "cmt_data", "%s.cgi" % gul)
    if not os.path.exists(p):
        return ""
    first = read(p).splitlines()[0] if os.path.getsize(p) else ""
    parts = first.split("|")
    raw = parts[4] if len(parts) > 4 else ""
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</p>", "\n", raw)
    txt = TAG.sub("", raw)
    txt = html.unescape(txt)
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


IMG_EXT = {"jpg", "jpeg", "png", "gif", "webp"}


def cmt_fields(bid, gul):
    """cmt_data/<gul>.cgi 첫 줄을 | 로 나눈 필드. [4]본문 [5]링크 [6]삽입이미지."""
    p = os.path.join(SP, "id", bid, "cmt_data", "%s.cgi" % gul)
    if not os.path.exists(p) or not os.path.getsize(p):
        return []
    return read(p).splitlines()[0].split("|")


def gul_order(bid):
    idx = os.path.join(SP, "id", bid, "idx", "idx.txt")
    if os.path.exists(idx):
        out = []
        for ln in read(idx).splitlines():
            ln = ln.strip()
            if ln.isdigit():
                out.append(ln)
        if out:
            return out
    # 대안: sub_data 파일명을 숫자 내림차순
    d = os.path.join(SP, "id", bid, "sub_data")
    gs = [f[:-4] for f in os.listdir(d) if f.endswith(".cgi") and f[:-4].isdigit()] if os.path.isdir(d) else []
    return sorted(gs, key=int, reverse=True)


def safe(name):
    name = os.path.basename(name)
    return re.sub(r"[^0-9A-Za-z._-]", "_", name)


missing_files = []


def process_board(bid):
    posts = []
    sub_dir = os.path.join(SP, "id", bid, "sub_data")
    files_dir = os.path.join(SP, "id", bid, "files")
    out_files = os.path.join(OUT, "assets", "boards", bid)
    for gul in gul_order(bid):
        sp = os.path.join(sub_dir, "%s.cgi" % gul)
        if not os.path.exists(sp):
            continue
        parts = read(sp).split("|")
        title = parts[3].strip() if len(parts) > 3 else ""
        date = fmt_date(parts[4]) if len(parts) > 4 else ""
        attach = parts[7].strip() if len(parts) > 7 else ""
        if not title:
            continue
        body = body_of(bid, gul)
        rel = None
        if attach:
            src = os.path.join(files_dir, attach)
            if os.path.exists(src):
                os.makedirs(out_files, exist_ok=True)
                fn = "%s__%s" % (gul, safe(attach))
                shutil.copy2(src, os.path.join(out_files, fn))
                rel = "assets/boards/%s/%s" % (bid, fn)
            else:
                missing_files.append("%s/%s (%s)" % (bid, gul, attach))
        posts.append({"gul": int(gul), "title": title, "date": date, "body": body, "file": rel})
    return posts


def fm_escape(v):
    # front matter 값에 콜론/따옴표가 있어도 안전하게
    v = (v or "").replace("\n", " ").strip()
    if re.search(r'[:#"]', v) or v != v.strip():
        return '"%s"' % v.replace('"', "'")
    return v


def write_md(folder, gul, title, date, file_rel, body):
    d = os.path.join(CONTENT, folder)
    os.makedirs(d, exist_ok=True)
    lines = ["---", "title: " + fm_escape(title), "date: " + (date or "")]
    if file_rel:
        lines.append("file: " + file_rel)
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
    with open(os.path.join(d, "%s.md" % gul), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def copytree(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True
    return False


def main():
    print("public_html:", PUB)
    print("출력:", OUT, "\n")

    # 1) 강의 게시판 → content/courses/<id>/*.md
    for name, bid in COURSES:
        posts = process_board(bid)
        got = sum(1 for p in posts if p["file"])
        for p in posts:
            write_md(os.path.join("courses", bid), p["gul"], p["title"], p["date"], p["file"], p["body"])
        print("[%s] 글 %d건, 첨부 %d건" % (name, len(posts), got))

    # 2) News (cclab 게시판) → content/news/*.md  (삽입 이미지·첨부 포함)
    n = nimg = 0
    news_assets = os.path.join(OUT, "assets", "news")
    sshot = os.path.join(SP, "id", "cclab", "screen_shot")
    cfiles = os.path.join(SP, "id", "cclab", "files")

    def copy_news(srcdir, name):
        src = os.path.join(srcdir, name)
        if not os.path.exists(src):
            return None
        os.makedirs(news_assets, exist_ok=True)
        fn = safe(name)
        shutil.copy2(src, os.path.join(news_assets, fn))
        return "assets/news/" + fn

    for gul in gul_order("cclab"):
        sp = os.path.join(SP, "id", "cclab", "sub_data", "%s.cgi" % gul)
        if not os.path.exists(sp):
            continue
        parts = read(sp).split("|")
        title = parts[3].strip() if len(parts) > 3 else ""
        date = fmt_date(parts[4]) if len(parts) > 4 else ""
        if not title:
            continue
        attach = parts[7].strip() if len(parts) > 7 else ""
        cf = cmt_fields("cclab", gul)
        url = cf[5].strip() if len(cf) > 5 else ""
        inline_img = cf[6].strip() if len(cf) > 6 else ""
        imgs, file_ref = [], None
        if inline_img:
            rel = copy_news(sshot, inline_img)
            if rel:
                imgs.append(rel); nimg += 1
        if attach:
            rel = copy_news(cfiles, attach)
            if rel:
                ext = attach.rsplit(".", 1)[-1].lower() if "." in attach else ""
                if ext in IMG_EXT:
                    imgs.append(rel); nimg += 1
                else:
                    file_ref = rel
        bparts = []
        if body_of("cclab", gul):
            bparts.append(body_of("cclab", gul))
        if url.startswith("http"):
            bparts.append("[관련 링크](%s)" % url)
        for im in imgs:
            bparts.append("![](%s)" % im)
        write_md("news", gul, title, date, file_ref, "\n\n".join(bparts))
        n += 1
    print("\nNews 글 %d건 (이미지/첨부 %d개)" % (n, nimg))

    # 3) Publications — 원본 publications.html → content/publications/<번호>.md
    pub_src = os.path.join(PUB, "publications", "publications.html")
    if os.path.exists(pub_src):
        pt = dec(open(pub_src, "rb").read())
        blocks = re.findall(r'<LI value="(\d+)">(.*?)</LI>', pt, re.S | re.I)
        npub = nppdf = 0
        for num, inner in blocks:
            m = re.search(r'href="\.?/?papers/([^"]+)"', inner, re.I)
            cite = re.sub(r'<a\s[^>]*href="\.?/?papers/[^"]+"[^>]*>.*?</a>', "", inner, flags=re.S | re.I)
            cite = re.sub(r"(?i)<br\s*/?>", " ", cite)
            cite = re.sub(r"\s+", " ", cite).strip()
            # 원본에서 하이픈이 '?'로 깨진 경우 교정 (글자-글자 사이의 ?만)
            cite = re.sub(r"(?<=[\wͰ-Ͽ])\?(?=[\wͰ-Ͽ])", "-", cite)
            yrs = re.findall(r"\((\d{4})\)", cite)
            year = yrs[-1] if yrs else ""
            pdf = m.group(1) if m else None
            d = os.path.join(CONTENT, "publications")
            os.makedirs(d, exist_ok=True)
            lines = ["---", "num: " + num, "year: " + year]
            if pdf:
                lines.append("pdf: " + pdf)
                nppdf += 1
            lines += ["---", "", cite]
            with open(os.path.join(d, "%03d.md" % int(num)), "w", encoding="utf-8") as f:
                f.write("\n".join(lines).rstrip() + "\n")
            npub += 1
        print("Publications %d편 (PDF %d편)" % (npub, nppdf))

    # 4) 이미지/논문 PDF 를 사이트 안으로 복사
    print("\n이미지·논문 복사 중...")
    copytree(os.path.join(PUB, "images"), os.path.join(OUT, "assets", "images"))
    copytree(os.path.join(PUB, "people", "photos"), os.path.join(OUT, "assets", "people", "photos"))
    copytree(os.path.join(PUB, "research"), os.path.join(OUT, "assets", "research"))
    copytree(os.path.join(PUB, "publications", "papers"), os.path.join(OUT, "assets", "publications", "papers"))

    # 4) 사이트 생성 (로컬 자산 모드)
    print("사이트 생성 중...")
    env = dict(os.environ, CCLAB_LOCAL="1")
    subprocess.run([sys.executable, os.path.join(GEN, "build.py"), OUT], check=True, env=env)

    print("\n완료.")
    print("게시글은 '%s' 아래 Markdown 파일로 저장했습니다." % CONTENT)
    print("  - content/news/*.md            소식")
    print("  - content/courses/<게시판>/*.md  강의자료")
    print("새 글을 추가하려면 해당 폴더에 .md 파일을 만들고,")
    print("  CCLAB_LOCAL=1 python3 _generator/build.py .  를 다시 실행하세요.")
    if missing_files:
        print("\n첨부가 덤프에 없어 링크하지 못한 글 %d건 (genchem/natsci 는 서버에서 이미 유실):" % len(missing_files))
        for x in missing_files[:10]:
            print("  -", x)
    print("\n이제 '%s' 폴더를 GitHub Pages 저장소에 올리면 됩니다." % OUT)


if __name__ == "__main__":
    main()
