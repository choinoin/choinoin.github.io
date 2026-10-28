# CCLab@KNU 홈페이지 (GitHub Pages)

강원대학교 화학과 전산화학연구실 홈페이지입니다. 빌드 과정 없이 HTML/CSS만으로 동작합니다.

## 게시 방법

1. GitHub에서 저장소를 만듭니다.
   - `<계정>.github.io` 이름으로 만들면 `https://<계정>.github.io/` 주소가 됩니다.
   - 다른 이름(예: `cclab`)이면 `https://<계정>.github.io/cclab/` 주소가 됩니다.
2. 이 폴더의 파일을 모두 저장소 루트에 올립니다 (`.nojekyll` 포함).
3. 저장소 **Settings → Pages** 에서 Source를 `Deploy from a branch`, 브랜치 `main`, 폴더 `/ (root)` 로 지정합니다.
4. 1~2분 뒤 위 주소에서 확인합니다.

## 구조

| 경로 | 내용 |
|---|---|
| `index.html` | 홈 (소개, 최근 소식, 연락처) |
| `people/` | 교수 약력, 구성원, 졸업생, 사진 |
| `research/` | 연구 분야 (한국어/English 전환) |
| `publications/` | 논문 목록 (검색 가능) |
| `news/` | 연구실 소식 |
| `courses/` | 강의 목록 |
| `assets/style.css` | 공통 스타일 |

모든 링크가 상대 경로라서 어느 저장소 이름으로 올려도 그대로 동작합니다.

## 수정하는 법

- **소식 추가**: `news/index.html`의 `<ul class="news-list">` 맨 위에 한 줄 추가
  ```html
  <li><time>2026.10.28</time><span>새 소식 제목</span></li>
  ```
  홈 화면 소식(`index.html`)에도 같은 줄을 추가하고 가장 오래된 줄을 지웁니다.
- **논문 추가**: `publications/index.html`에서 해당 연도 `<ol class="pubs">` 맨 위에 `<li>` 하나를 복사해 수정합니다. `data-n` 은 번호입니다.
- **구성원 변경**: `people/index.html`의 Members / Alumni 부분을 수정합니다.

## 이미지에 대해

사진과 연구 그림은 현재 기존 서버(`www2.kangwon.ac.kr/~cclab`)의 주소를 그대로 불러옵니다.
기존 서버가 닫히면 해당 이미지는 자동으로 숨겨집니다. 계속 쓰려면 이미지를 `assets/images/`에 넣고 HTML의 `src` 주소를 바꿔 주세요.
