# docs/

연구 계획, 회의록, 참고 자료 등 문서 폴더.

## 폴더 소개

- **What**: 프로젝트 계획서, 교수님 피드백, 회의록, 참고 문헌 등
- **Why**: 코드와 분리해 연구 진행 맥락을 기록/관리하기 위함
- `private/` 하위는 개인정보·비공개 자료로 **git 추적 제외**

## 하위 구조

```
docs/
├── README.md  STYLE_GUIDE.md  NOTION_WORKSPACE.md  TEAM_ONBOARDING.html
├── research_design/             # 확정된 연구 설계 (Source of Truth)
│   ├── research_plan.html               # 연구 전체 설계, Baseline→H1→H2→H3 스토리
│   └── research_gap_contribution.html   # 선행연구 공백 + 우리 연구의 기여
├── meetings/                     # 회의 기록, 날짜 중심 파일명
│   └── YYYYMMDD_meeting.html
├── feedback/                     # 교수님 피드백 반영 계획
│   └── 1st_professor_feedback_plan.html
├── templates/                    # STYLE_GUIDE 기반 템플릿
└── private/                      # git 추적 제외
    ├── 프로젝트 계획서.docx      # 팀원 개인 일정 등 포함
    └── 교수님 피드백.pdf         # 비공개 피드백
```

`research_design/`은 확정된 설계만 담고(진행 과정·역할분담은 `meetings/`), `meetings/`는 그날 논의된 내용을 그대로 보존하되 계속 유효한 규칙은 `STYLE_GUIDE.md`로 옮겨 적는다. 개인정보나 비공개 내용이 섞인 원본은 `docs/private/`에 둔다.
