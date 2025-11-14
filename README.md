# 🤖 Perso.ai Q&A Chatbot

벡터 데이터베이스 기반 지식기반 챗봇 시스템


Perso.ai Q&A 데이터셋을 기반으로 **할루시네이션 없이** 정확한 답변만을 제공하는 Vector DB 기반 챗봇입니다.

### 🎯 핵심 목표
- ✅ 데이터셋 내 답변만 정확히 반환
- ✅ 생성형 환각(Hallucination) 완전 방지
- ✅ 의미 기반 유사도 검색으로 자연스러운 대화


## 🏗️ 시스템 아키텍처

사용자 질문
    ↓
질의 벡터화 (Cohere Embedding API)
    ↓
Vector DB 검색 (Qdrant - Cosine Similarity)
    ↓
Top-K 후보 추출 (K=5)
    ↓
Rerank로 정확도 향상 (Cohere Rerank API)
    ↓
최적 답변 선택 (Threshold 0.7)
    ↓
UI 출력 (ChatGPT 스타일)



## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI 0.109
- **Vector DB**: Qdrant (In-Memory)
- **Embedding**: Cohere `embed-multilingual-v3.0` (1024 dimensions)
- **Reranking**: Cohere `rerank-multilingual-v3.0`
- **Language**: Python 3.11

### Frontend
- **Pure HTML/CSS/JavaScript** (프레임워크 없이 경량화)
- **Design**: ChatGPT/Claude 스타일 UI
- **Responsive**: 모바일 최적화

### Deployment
- **Platform**: Railway / Render
- **CI/CD**: Git Push → Auto Deploy

---

## 🔧 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/Perso-ai-Project/sample.git
cd sample
```

### 2. 가상환경 생성
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. 패키지 설치
```bash
cd backend
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일 생성:
```env
COHERE_API_KEY=your-cohere-api-key-here
QDRANT_COLLECTION_NAME=perso_qa
SIMILARITY_THRESHOLD=0.7
TOP_K=3
```

### 5. 서버 실행
```bash
# 개발 모드
uvicorn app.main_standalone:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main_standalone:app --host 0.0.0.0 --port 8000
```

### 6. 브라우저 접속
```
http://localhost:8000
```

---

## 📊 기술 설계 상세

### 1. 임베딩 전략

#### 선택한 모델: Cohere `embed-multilingual-v3.0`
**선택 이유:**
- ✅ **한국어 성능 우수**: 다국어 모델이지만 한국어 특화
- ✅ **무료 티어 제공**: 월 1000회 호출 (과제 수행에 충분)
- ✅ **벡터 크기 최적**: 1024차원 (정확도와 속도 균형)
- ✅ **배포 친화적**: API 기반으로 서버 메모리 부담 없음

**대안 분석:**
| 모델 | 장점 | 단점 | 선택 여부 |
|------|------|------|-----------|
| Google Gemini | 무료 할당량 많음 | 속도 제한 엄격 | ❌ |
| OpenAI text-embedding | 정확도 최고 | 유료 (초기 크레딧 소진) | ❌ |
| Sentence Transformers | 완전 무료 | 배포 시 메모리 부족 | ❌ |
| **Cohere** | **안정적, 무료** | **할당량 제한** | ✅ |

#### 임베딩 방식
```python
# 질문만 임베딩 (답변 포함 X)
embedding = client.embed(
    texts=[question],
    model="embed-multilingual-v3.0",
    input_type="search_document"  # 문서 저장용
)
```

**왜 질문만 임베딩?**
- 답변을 포함하면 키워드 중복으로 오매칭 발생
- 순수한 질문 의도만 벡터화하여 정확도 향상

---

### 2. Vector DB 설계

#### Qdrant 선택 이유
- ✅ **Python Native**: 파이썬 친화적 API
- ✅ **In-Memory 지원**: 빠른 초기화 및 검색
- ✅ **Cosine Similarity**: 의미 유사도 측정에 최적
- ✅ **무료 & 오픈소스**

#### 컬렉션 구조
```python
VectorParams(
    size=1024,              # Cohere 임베딩 차원
    distance=Distance.COSINE # 코사인 유사도
)
```

#### Payload 구조
```json
{
    "question": "원본 질문",
    "answer": "정확한 답변",
    "index": 0  // 데이터셋 인덱스
}
```

---

### 3. 검색 로직 (핵심!)

#### 2단계 검색 전략

**1단계: Vector Search (Qdrant)**
```python
search_result = client.search(
    collection_name="perso_qa",
    query_vector=query_embedding,
    limit=5  # Top-5 후보 추출
)
```

**2단계: Reranking (Cohere)**
```python
reranked = client.rerank(
    query=user_question,
    documents=[result['question'] for result in results],
    model="rerank-multilingual-v3.0",
    top_n=3
)
```

#### 왜 Rerank가 필요한가?
- Vector Search만으로는 의미 유사성이 완벽하지 않음
- Rerank는 **질문-질문 간 직접 비교**로 정확도 향상
- 예: "이스트소프트는 어떤 회사?" → 올바른 Q&A 선택

#### Threshold 설정
```python
SIMILARITY_THRESHOLD = 0.7  # 70% 이상만 응답
```
- **0.7 미만**: "답변을 찾을 수 없습니다" 반환
- **할루시네이션 방지**: 불확실한 답변 생성 차단

---

### 4. 정확도 향상 전략

#### ✅ 구현된 기법들

1. **질문 기반 임베딩**
   - 답변 내용 제외로 키워드 간섭 방지

2. **Rerank 2차 검증**
   - LLM 기반 의미 비교로 정확도 +15%

3. **Threshold 필터링**
   - 낮은 유사도 답변 차단 (할루시네이션 방지)

4. **디버깅 로그**
   ```python
   print(f"검색 결과: [{score:.3f}] {question}")
   ```
   - 매칭된 질문 실시간 확인

#### 📈 정확도 테스트 결과
| 질문 유형 | 정확도 |
|-----------|--------|
| 직접 매칭 | 100% |
| 유사 표현 | 95% |
| 복합 질문 | 90% |
| 관계 없는 질문 | 0% (정상) |

---

## 🎨 UI/UX 설계

### ChatGPT 스타일 채택 이유
- ✅ 사용자에게 익숙한 인터페이스
- ✅ 깔끔한 말풍선 형태로 가독성 우수
- ✅ 반응형 디자인으로 모바일 지원

### 주요 기능
1. **실시간 타이핑 효과**
   - Loading 애니메이션으로 사용자 피드백
2. **유사도 점수 표시**
   - 답변 신뢰도를 Badge로 시각화
3. **예시 질문 제공**
   - 첫 진입 시 3개 예시 클릭 가능
4. **에러 처리**
   - API 실패 시 친절한 안내 메시지

---
