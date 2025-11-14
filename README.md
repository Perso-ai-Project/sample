# 🤖 Perso.ai Q&A Chatbot

벡터 데이터베이스 기반 지식기반 챗봇 시스템

Perso.ai Q&A 데이터셋을 기반으로 **할루시네이션 없이** 정확한 답변만을 제공하는 Vector DB 기반 챗봇입니다.

### 🎯 핵심 목표
- ✅ 데이터셋 내 답변만 정확히 반환
- ✅ 생성형 환각(Hallucination) 완전 방지
- ✅ 의미 기반 유사도 검색으로 자연스러운 대화

---

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

---

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI 0.109
- **Vector DB**: Qdrant (In-Memory)
- **Embedding**: Cohere `embed-multilingual-v3.0` (1024 dimensions)
- **Reranking**: Cohere `rerank-multilingual-v3.0`
- **Language**: Python 3.11

### Frontend
- **Pure HTML/CSS/JavaScript**
- **Design**: ChatGPT/Claude 스타일
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

2. 가상환경 생성
 ``` bash

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
 ```

3. 패키지 설치
 ``` bash
cd backend
pip install -r requirements.txt
 ``` 
4. 환경변수 설정
.env 파일 생성:
``` bash
COHERE_API_KEY=your-cohere-api-key-here
QDRANT_COLLECTION_NAME=perso_qa
SIMILARITY_THRESHOLD=0.7
TOP_K=3
 ```

5. 서버 실행
 ``` bash
uvicorn app.main_standalone:app --reload --host 0.0.0.0 --port 8000
 ```
6. 브라우저 접속
 ``` bash
http://localhost:8000
 ```

임베딩 전략
모델: Cohere embed-multilingual-v3.0
선택 이유

한국어 성능 우수

무료 티어 제공

1024차원으로 적절한 정확도/속도

API기반이라 서버메모리 부담 없음

임베딩 방식
 ``` bash
embedding = client.embed(
    texts=[question],
    model="embed-multilingual-v3.0",
    input_type="search_document"
)
 ```

질문만 임베딩하는 이유

답변 포함 시 키워드 충돌 발생

질문의 의도만 벡터화해야 정확도 증가

