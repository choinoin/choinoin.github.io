# CCLab@KNU 홈페이지 — 빌드 툴킷

강원대학교 화학과 전산화학연구실 홈페이지입니다. 기존 서버(PHP/CGI·세팔보드) 없이
GitHub Pages에서 그대로 돌아갑니다. **모든 글은 `content/` 폴더의 파일로 관리**하고,
사이트의 **글쓰기** 메뉴로 파일을 만들 수도 있습니다.

## 1) 처음 한 번 — public_html 에서 내용 가져오기 (마이그레이션)

서버에서 받아둔 `public_html` 로 글·첨부·이미지를 한 번에 옮깁니다. Python 3만 있으면 됩니다.

```
python3 process_local.py /받아둔/public_html
```

생성/복사되는 것:
- `content/news/*.md` — 소식
- `content/courses/<게시판>/*.md` — 강의자료 (+ `assets/boards/…` 에 첨부 PDF)
- `content/publications/*.md` — 논문 94편 (+ `assets/publications/papers/…` 에 논문 PDF)
- `assets/images`, `assets/people/photos` — 로고·사진
- **People(교수·구성원·졸업생·사진)** 정보는 이미 `content/people/` 에 들어 있습니다.
- **비밀번호·회원정보·IP·관리자 설정은 포함하지 않습니다** (아래 보안 항목).

> 다시 실행하면 news/courses/publications 가 원본 기준으로 덮어써집니다.
> **마이그레이션은 처음 한 번만** 하고, 이후에는 2)번으로 관리하세요.
> (`content/people/` 은 마이그레이션이 건드리지 않으니 안심하고 편집해도 됩니다.)

## 2) 글 추가·수정하기

### 방법 1 — 사이트의 "✎ 글쓰기" 메뉴 (제일 쉬움)

사이트 상단 **글쓰기** 페이지에서 구분(News/Courses/Publications)·제목·날짜·본문·첨부파일을 넣고
**zip 다운로드**를 누르면, 올바른 경로의 MD 파일과 첨부가 담긴 zip이 내려받아집니다.
그 zip을 **사이트 폴더(저장소) 루트에 풀어넣고** 커밋(또는 다시 빌드)하면 끝입니다.
- 크롬·엣지에서는 **"폴더에 바로 저장"** 버튼으로 압축 해제 없이 사이트 폴더에 바로 쓸 수도 있습니다.

### 방법 2 — 파일 직접 편집

`content/` 아래 파일을 직접 만들거나 고쳐도 됩니다.

- **소식**: `content/news/제목.md`
  ```
  ---
  title: 새 소식
  date: 2026.10.29
  ---
  본문을 **마크다운**으로.
  ```
- **강의자료**: `content/courses/<게시판>/제목.md` (+ PDF를 `assets/boards/<게시판>/` 에)
  ```
  ---
  title: 2026 통계역학 1장
  date: 2026.03.02
  file: assets/boards/statmech/note.pdf
  ---
  ```
- **논문**: `content/publications/번호.md`
  ```
  ---
  num: 95
  year: 2026
  pdf: myposter.pdf
  ---
  A. Author, ..., and H. Hwang, "Title", J. Name <b>12</b>, 345 (2026).
  ```
  (논문 PDF는 `assets/publications/papers/` 에 두세요. `num` 없는 새 글은 해당 연도 맨 위에 표시됩니다.)
- **구성원**: `content/people/members/<그룹>-<순번>-<이름>.md`
  ```
  ---
  name: 홍길동
  group: grad       # postdoc / grad / undergrad
  role: 석사과정
  order: 4
  email:            # 선택
  research:         # 선택
  photo:            # 선택: people/photos/파일.jpg
  ---
  ```
  졸업생은 `content/people/alumni.md` 에 `이름 | 과정·기간` 한 줄 추가, 사진은 `content/people/gallery.md`.

## GitHub Pages 올리기 — 자동 빌드 (권장)

`.github/workflows/pages.yml` 이 들어 있어, **GitHub에 커밋하면 자동으로 빌드·게시**됩니다.
1. 저장소 생성 → 이 폴더의 파일을 모두 올립니다(`.github/`, `content/` 포함).
2. Settings → Pages → **Source: GitHub Actions**.
3. 이후 `content/` 에 글(.md)과 첨부를 커밋하면 사이트가 자동 갱신됩니다.

직접 빌드하려면: `CCLAB_LOCAL=1 python3 _generator/build.py .` (미리보기: `python3 -m http.server 8000`).

## ⚠️ 보안 — 반드시 확인

받으신 `public_html` 에는 **민감 정보가 있습니다.** 이 사이트에는 포함하지 않지만,
`public_html` 원본을 **공개 저장소에 올리면 안 됩니다.**
- `cgi-bin/spboard/member/mem_data/*.cgi` — 게시판 계정 **비밀번호(평문)·이름·이메일·IP**
- 각 글 본문 파일(`cmt_data/*.cgi`) — 작성자 **비밀번호·IP·브라우저 정보**
- `admin_conf.cgi`, `setup.cgi`, 게시판별 `conf.cgi` — 관리자 설정
- 노출된 비밀번호는 **이미 유출됐다고 보고**, 재사용 중이면 바꾸세요.

## 구조

| 경로 | 내용 |
|---|---|
| 각 폴더의 `index.html`, `write.html` | 생성된 페이지 |
| `content/news`·`courses`·`publications`·`people` | **글·구성원 (여기만 편집)** |
| `assets/` | 스타일·이미지·첨부 PDF |
| `_generator/build.py` | 사이트 생성기 |
| `process_local.py` | public_html → content/ 마이그레이션 (처음 한 번) |
| `.github/workflows/pages.yml` | 커밋 시 자동 빌드 |

모달 크기는 `assets/style.css` 맨 위 `--modal-w`, `--modal-h` 로 조절합니다.
배경의 계절 애니메이션(가을 낙엽·겨울 눈 등)은 `assets/seasons.js` 가 담당하며, 화면 우하단 토글로도 켜고 끌 수 있습니다.


## 자료 열람 코드(cclab)

강의자료·논문 PDF 등 파일을 열 때 코드 `cclab` 을 입력해야 합니다(수강생 편의용 가벼운 잠금). 한 번 입력하면 그 브라우저에 기억됩니다. 코드를 바꾸려면 `assets/gate.js` 의 `CODE` 값을 수정하세요. 공개 저장소를 직접 아는 사람은 우회 가능하다는 점은 전제입니다.

## 반응형

모바일·태블릿·데스크톱·고해상도를 지원합니다. 좁은 화면에서는 상단 메뉴가 햄버거(≡)로 바뀌고, 카드·폼·모달이 화면폭에 맞춰 세로로 재배치됩니다. 320px 폭까지 가로 스크롤 없이 동작합니다.
