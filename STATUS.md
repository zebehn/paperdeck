---
project: paperdeck
purpose: PDF 논문을 입력받아 대규모 언어 모델로 Beamer 발표자료 LaTeX 코드를 생성하는 명령줄 도구를 만든다.
owner: [미확인]
status: 대기
stage: 명령줄 도구 0.1.0이 OpenAI 제공자 기준으로 동작하는 상태에서 2026-01-22 이후 개발이 멈춰 있고, 유지·확장 방향에 대한 사용자 결정을 기다린다 (기준일 2026-09-25). [현황 미확인, 2026-09-25 점검]
updated: 2026-09-25
next:
  - "[사용자] 유지·확장 방향 결정"
  - 테스트 모음을 실행해 현재 통과 수를 확인
  - 현재 OpenAI 모델과 DocScalpel 최신판으로 논문 1편 종단 실행을 점검
  - README의 AI 제공자 지원 표기를 구현 상태에 맞게 정리
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

> 기재 정책: zebehn/mastermind docs/STATUS_POLICY.md (v1.1). 주 담당 [미확인]. 최종 갱신 2026-09-25 (KST).

## 요약

PaperDeck은 PDF 논문을 Beamer 발표자료로 바꾸는 Python 명령줄 도구다.
2026-01-22 이후 커밋이 없고, 유지·확장 방향에 대한 사용자 결정을 기다린다.
가장 가까운 다음 단계는 방향 결정과 현재 환경에서의 종단 실행 점검이다.

## 현재 단계

- 버전은 0.1.0이다 (pyproject.toml 기준).
- 처리 순서는 PDF 본문 추출(PyMuPDF), 그림·표 추출(DocScalpel 명령줄 호출), 언어 모델 호출, Beamer LaTeX 생성, pdflatex 컴파일이다.
- 명령은 generate, list-prompts, version 세 가지다.
- 내장 프롬프트 템플릿은 default, complete, single-element, hangeul 네 가지다.
- 생성된 LaTeX의 환경 짝·괄호 짝을 점검하고 자동 수정하는 검증 모듈이 있다.
- 구현된 AI 제공자는 OpenAI 하나다. 기본 모델은 코드상 gpt-5.1이다.
- Anthropic, Ollama, LM Studio 제공자는 선택지로만 있고 호출 시 NotImplementedError를 낸다.
- README는 네 제공자를 모두 지원한다고 적고 있어 구현과 다르다.
- 설정 파일 읽기·저장, 수식 슬라이드 생성, 사용자 프롬프트 저장·삭제는 코드에 TODO로 남아 있다.
- 테스트 통과 수는 README 배지 95개, CHANGELOG 141개로 서로 다르다. 현재 통과 수는 [미확인].
- 실제 사용 빈도와 마지막 사용일은 [미확인].

## 최근 진행

- 2026-01-22 DocScalpel 명령줄 도구 감지 방식 개선
- 2026-01-10 문서 파일을 docs/ 폴더로 이동
- 2026-01-10 LaTeX 괄호 짝 점검과 자동 수정 기능 병합
- 2026-01-08 그림·표마다 설명 슬라이드와 그림 슬라이드를 따로 두는 single-element 템플릿 추가
- 2025-12-31 Beamer 캡션 구문 오류 수정

## 다음 할 일

- [사용자] 유지·확장 방향 결정
- 테스트 모음을 실행해 현재 통과 수를 확인
- 현재 OpenAI 모델과 DocScalpel 최신판으로 논문 1편 종단 실행을 점검
- README의 AI 제공자 지원 표기를 구현 상태에 맞게 정리

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
