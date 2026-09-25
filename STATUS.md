---
project: paperdeck
purpose: PDF 논문을 입력받아 대규모 언어 모델로 Beamer 발표자료 LaTeX 코드를 생성하는 명령줄 도구를 만든다.
owner: 크리스티앙 (GPU 서버)
status: 대기
stage: 명령줄 도구 0.1.0은 2026-01-22 이후 개발이 멈춰 있다. 2026-09-25 테스트 모음 점검에서 415개 통과, 24개 실패, 27개 건너뜀이 나왔고, 유지·확장 방향에 대한 사용자 결정을 기다린다 (기준일 2026-09-25).
updated: 2026-09-25
next:
  - "[사용자] 유지·확장 방향 결정"
  - 실패 테스트 24개의 원인을 코드 결함과 오래된 테스트로 나눠 정리
  - OpenAI API 키, pdflatex, DocScalpel을 갖춘 환경에서 논문 1개 종단 실행을 점검
  - reportlab을 requirements-dev.txt에 추가
decisions:
  - 유지·확장 방향 (계속 개발, 현 상태 유지, 보관 중 선택)
blockers: []
resources: []
related:
  - docscalpel
docs:
  - README.md
  - docs/CHANGELOG.md
  - docs/QUICKSTART.md
---

# PaperDeck 현황

> 기재 정책: zebehn/mastermind docs/STATUS_POLICY.md (v1.1). 주 담당 크리스티앙 (GPU 서버). 최종 갱신 2026-09-25 (KST).

## 요약

PaperDeck은 PDF 논문을 Beamer 발표자료로 바꾸는 Python 명령줄 도구다.
2026-09-25 점검에서 테스트 466개 중 415개가 통과했고, 유지·확장 방향에 대한 사용자 결정을 기다린다.
가장 가까운 다음 단계는 방향 결정과 실패 테스트 원인 정리다.

## 현재 단계

- 버전은 0.1.0이다 (pyproject.toml 기준).
- 처리 순서는 PDF 본문 추출(PyMuPDF), 그림·표 추출(DocScalpel 명령줄 호출), 언어 모델 호출, Beamer LaTeX 생성, pdflatex 컴파일이다.
- 명령은 generate, list-prompts, version 세 가지다.
- 내장 프롬프트 템플릿은 default, complete, single-element, hangeul 네 가지다.
- 생성된 LaTeX의 환경 짝·괄호 짝을 점검하고 자동 수정하는 검증 모듈이 있다.
- 구현된 AI 제공자는 OpenAI 하나다. 기본 모델은 코드상 gpt-5.1이다.
- Anthropic, Ollama, LM Studio 제공자는 선택지로만 있고 호출 시 NotImplementedError를 낸다.
- README·QUICKSTART·CHANGELOG의 제공자 표기를 2026-09-25에 구현 상태(OpenAI만 구현)에 맞게 고쳤다.
- 설정 파일 읽기·저장, 수식 슬라이드 생성, 사용자 프롬프트 저장·삭제는 코드에 TODO로 남아 있다.
- 테스트 결과(2026-09-25, GPU 서버, Linux, Python 3.11, docscalpel·pdflatex 미설치, GPU 미사용): 415개 통과, 24개 실패, 27개 건너뜀.
- 실패 24개 중 14개는 텍스트 추출 테스트이며, 모의 객체를 쓴 테스트에서 추출기가 "File not found"로 실패한다.
- 나머지 실패는 OpenAI 어댑터 테스트 4개(모의 대상 속성 없음, 키 형식 검사 등), 생성기 테스트 5개, 설정 기본값 테스트 1개(0.75 기대, 실제 0.5), 검증 파이프라인 테스트 1개다.
- 건너뜀 27개는 테스트 코드에 "Implementation not complete" 또는 docscalpel 필요로 표시된 항목이다.
- 테스트 준비 코드(conftest.py)는 reportlab을 쓰지만 requirements-dev.txt에 없다.
- 이 서버에는 pdflatex와 docscalpel 명령이 없고 OpenAI API 키도 설정돼 있지 않다.
- OpenAI 키 없음으로 종단 실행은 생략했다.
- README 배지와 CHANGELOG의 테스트 수는 2026-09-25 측정값을 조건과 함께 적도록 고쳤다.
- 실제 사용 빈도와 마지막 사용일은 [미확인].

## 최근 진행

- 2026-09-25 README·QUICKSTART·CHANGELOG의 AI 제공자 표기와 테스트 수를 구현·측정값에 맞게 수정
- 2026-09-25 테스트 모음 점검: 415개 통과, 24개 실패, 27개 건너뜀 (Python 3.11, docscalpel·pdflatex 미설치)
- 2026-09-25 주 담당을 크리스티앙 (GPU 서버)으로 인계(사용자 지시)
- 2026-01-22 DocScalpel 명령줄 도구 감지 방식 개선
- 2026-01-10 문서 파일을 docs/ 폴더로 이동

## 다음 할 일

- [사용자] 유지·확장 방향 결정
- 실패 테스트 24개의 원인을 코드 결함과 오래된 테스트로 나눠 정리
- OpenAI API 키, pdflatex, DocScalpel을 갖춘 환경에서 논문 1개 종단 실행을 점검
- reportlab을 requirements-dev.txt에 추가

## 결정 대기

- 유지·확장 방향 (계속 개발, 현 상태 유지, 보관 중 선택)
  - 계속 개발: 미구현 제공자 추가와 README 정정을 진행한다.
  - 현 상태 유지: 필요할 때만 수정한다.
  - 보관: 저장소를 보관 처리한다.

## 차단 요인

- 없음

## 핵심 문서

- [README.md](README.md): 설치, 명령, 설정, 템플릿 설명
- [docs/CHANGELOG.md](docs/CHANGELOG.md): 변경 이력 (0.1.0 항목까지 기재)
- [docs/QUICKSTART.md](docs/QUICKSTART.md): 빠른 시작 안내

## 관련 저장소

- docscalpel: PDF에서 그림·표를 잘라내는 도구이며, PaperDeck이 의존성으로 설치해 명령줄로 호출한다.
