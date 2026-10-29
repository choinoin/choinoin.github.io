# 마크다운 확장 + 코드 색상 업데이트 적용법

이 zip 안의 파일을 **저장소 루트(현재 `index.html`, `_generator`, `assets`, `content` 가 보이는 폴더)에 그대로 덮어쓰기**로 풀면 됩니다. `content/`(글·구성원)는 건드리지 않으니 안전합니다.

포함 파일:
- `_generator/build.py` — 변환기 교체(기존 파일 덮어씀)
- `assets/style.css` — 스타일 교체(기존에 코드블록·표·인용 스타일이 추가된 버전)
- `assets/hl-init.js` — 코드 색상 초기화(신규)
- `assets/highlight/…` — highlight.js v11.11.1 로컬 내장(신규)

## 적용 순서

```bash
cd <저장소 루트>          # index.html 이 보이는 폴더
# (zip 을 이 위치에 덮어쓰기로 풀기)

python3 _generator/build.py .   # content/*.md → HTML 재생성

git add -A
git commit -m "add rich markdown + code syntax highlighting"
git push
```

> ⚠️ 이 사이트는 push 만으로는 자동 빌드되지 않습니다(브랜치에서 바로 배포 모드).
> 반드시 **위처럼 로컬에서 재빌드한 HTML까지 함께 커밋**해야 사이트에 반영됩니다.

## 이제 쓸 수 있는 마크다운

```
# 제목   ## 소제목
**굵게**   *기울임*   _기울임_   `인라인코드`
- 글머리 목록      1. 번호 목록
> 인용문
---                (구분선)

| 머리1 | 머리2 | 머리3 |
|:---|:--:|---:|      (왼쪽 / 가운데 / 오른쪽 정렬)
| a | b | c |
```

## 코드블록 (색상 자동)

` ``` ` 로 감싸고 언어 이름을 적으면 변수·함수·문자열·주석이 색칠됩니다.
언어를 생략하면 자동 감지합니다.

````
```python
def f(x):
    return x ** 2   # 주석
```

```fortran
program p
  print *, "hello"
end program p
```
````

기본 지원 언어: Python, Fortran, MATLAB, C/C++, R, bash/shell, SQL, JavaScript 등
(highlight.js 공통 세트 + Fortran·MATLAB). 더 필요한 언어가 있으면
`assets/highlight/languages/` 에 해당 `*.min.js` 를 추가하고 `_generator/build.py` 의
`page()` 안 스크립트 목록에 한 줄 넣으면 됩니다.

## 글쓰기 "실제 미리보기"

글쓰기 페이지의 **실제 미리보기** 버튼도 위 문법·코드 색상을 사이트와 똑같이 보여줍니다.
