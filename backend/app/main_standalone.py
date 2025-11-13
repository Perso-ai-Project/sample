"""
Perso.ai Q&A Chatbot - Cohere API Version
배포에 최적화된 버전 (무료 API 사용)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
from functools import lru_cache
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import os

# ==================== 설정 ====================

class AppSettings(BaseSettings):
    COHERE_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "perso_qa"
    SIMILARITY_THRESHOLD: float = 0.7
    TOP_K: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings():
    return AppSettings()

settings = get_settings()

# ==================== 임베딩 서비스 ====================

class EmbeddingService:
    def __init__(self):
        if not settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY가 설정되지 않았습니다.")
        self.client = cohere.Client(settings.COHERE_API_KEY)
        self.model = "embed-multilingual-v3.0"  # 한국어 지원
        print(f"✅ Cohere 임베딩 서비스 초기화 완료")
    
    def get_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type="search_document"  # 문서 저장용
            )
            return response.embeddings[0]
        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {e}")
            raise
    
    def get_query_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type="search_query"  # 검색 쿼리용
            )
            return response.embeddings[0]
        except Exception as e:
            print(f"❌ 쿼리 임베딩 생성 실패: {e}")
            raise
    
    def rerank(self, query: str, documents: List[str]) -> List[Dict]:
        """Cohere Rerank API로 결과 재정렬"""
        try:
            response = self.client.rerank(
                query=query,
                documents=documents,
                model="rerank-multilingual-v3.0",
                top_n=3
            )
            return response.results
        except Exception as e:
            print(f"⚠️ Rerank 실패, 기본 결과 사용: {e}")
            return None

# ==================== 벡터 스토어 ====================

class VectorStore:
    def __init__(self, embedding_service: EmbeddingService):
        # 배포 환경에서는 :memory: 사용 (영구 저장 불필요)
        self.client = QdrantClient(location=":memory:")
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_service = embedding_service
        self.initialized = False
    
    def initialize_collection(self, vector_size: int):
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            self.initialized = True
            print(f"✅ 컬렉션 '{self.collection_name}' 생성 완료 (벡터 크기: {vector_size})")
        except Exception as e:
            print(f"❌ 컬렉션 생성 실패: {e}")
            raise
    
    def add_documents(self, qa_pairs: List[Dict[str, str]]):
        if not self.initialized:
            sample_embedding = self.embedding_service.get_embedding(qa_pairs[0]['question'])
            self.initialize_collection(vector_size=len(sample_embedding))
        
        points = []
        for idx, qa in enumerate(qa_pairs):
            # 질문만 임베딩 (정확한 매칭을 위해)
            embedding = self.embedding_service.get_embedding(qa['question'])
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "question": qa['question'],
                    "answer": qa['answer'],
                    "index": idx
                }
            )
            points.append(point)
            print(f"📝 처리 중: {idx + 1}/{len(qa_pairs)} - {qa['question'][:40]}...")
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"✅ 총 {len(points)}개의 Q&A 데이터 저장 완료\n")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        try:
            query_embedding = self.embedding_service.get_query_embedding(query)
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "question": hit.payload['question'],
                    "answer": hit.payload['answer'],
                    "score": hit.score,
                    "index": hit.payload['index']
                })
            return results
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            return []
    
    def get_best_answer(self, query: str) -> Optional[Dict]:
        # Top 3 결과를 가져와서 분석
        results = self.search(query, top_k=3)
        if not results:
            return None
        
        best_match = results[0]
        
        # 디버깅용 출력
        print(f"\n🔍 검색 결과 for '{query}':")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. [{r['score']:.3f}] {r['question'][:50]}...")
        
        # 유사도가 너무 낮으면 답변 못 찾음
        if best_match['score'] < settings.SIMILARITY_THRESHOLD:
            return {
                "question": query,
                "answer": "죄송합니다. 해당 질문에 대한 정확한 답변을 찾을 수 없습니다. Perso.ai에 대한 다른 질문을 해주세요.",
                "score": best_match['score'],
                "found": False
            }
        
        return {
            "question": best_match['question'],
            "answer": best_match['answer'],
            "score": best_match['score'],
            "found": True
        }

# ==================== FastAPI 앱 ====================

app = FastAPI(
    title="Perso.ai Q&A Chatbot API",
    description="벡터 데이터베이스 기반 지식기반 챗봇 (Cohere Embedding)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
embedding_service = None
vector_store = None

# Request/Response 모델
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    score: float
    found: bool

class HealthResponse(BaseModel):
    status: str
    message: str

# Q&A 데이터
QA_DATA = [
    {
        "question": "Perso.ai는 어떤 서비스인가요?",
        "answer": "Perso.ai는 이스트소프트가 개발한 다국어 AI 영상 더빙 플랫폼으로, 누구나 언어의 장벽 없이 영상을 제작하고 공유할 수 있도록 돕는 AI SaaS 서비스입니다."
    },
    {
        "question": "Perso.ai의 주요 기능은 무엇인가요?",
        "answer": "Perso.ai는 AI 음성 합성, 립싱크, 영상 더빙 기능을 제공합니다. 사용자는 원본 영상에 다른 언어로 음성을 입히거나, 입 모양까지 자동으로 동기화할 수 있습니다."
    },
    {
        "question": "Perso.ai는 어떤 기술을 사용하나요?",
        "answer": "Perso.ai는 ElevenLabs, Microsoft, Google Cloud Speech API 등과 같은 글로벌 기술 파트너의 음성합성 및 번역 기술을 활용하며, 자체 개발한 립싱크 엔진을 결합합니다."
    },
    {
        "question": "Perso.ai의 사용자는 어느 정도인가요?",
        "answer": "2025년 기준, 전 세계 누적 20만 명 이상의 사용자가 Perso.ai를 통해 AI 기반 영상 제작을 경험했습니다."
    },
    {
        "question": "Perso.ai를 사용하는 주요 고객층은 누구인가요?",
        "answer": "유튜버, 강의 제작자, 기업 마케팅 담당자 등 영상 콘텐츠를 다국어로 확장하려는 개인 및 기업 고객이 주요 타깃입니다."
    },
    {
        "question": "Perso.ai에서 지원하는 언어는 몇 개인가요?",
        "answer": "현재 30개 이상의 언어를 지원하며, 한국어, 영어, 일본어, 스페인어, 포르투갈어 등 주요 언어가 포함됩니다."
    },
    {
        "question": "Perso.ai의 요금제는 어떻게 구성되어 있나요?",
        "answer": "Perso.ai는 사용량 기반 구독 모델을 운영합니다. Free, Creator, Pro, Enterprise 플랜이 있으며 Stripe를 통해 결제할 수 있습니다."
    },
    {
        "question": "Perso.ai는 어떤 기업이 개발했나요?",
        "answer": "Perso.ai는 소프트웨어 기업 이스트소프트(ESTsoft)가 개발했습니다."
    },
    {
        "question": "이스트소프트는 어떤 회사인가요?",
        "answer": "이스트소프트는 1993년에 설립된 IT 기업으로, 알집, 알약, 알씨 등 생활형 소프트웨어로 잘 알려져 있으며, 최근에는 인공지능 기반 서비스 개발에 집중하고 있습니다."
    },
    {
        "question": "Perso.ai의 기술적 강점은 무엇인가요?",
        "answer": "AI 음성 합성과 립싱크 정확도가 높고, 다국어 영상 제작이 간편하며, 실제 사용자 인터페이스가 직관적이라는 점이 강점입니다."
    },
    {
        "question": "Perso.ai를 사용하려면 회원가입이 필요한가요?",
        "answer": "네, 이메일 또는 구글 계정으로 간단히 회원가입 후 서비스를 이용할 수 있습니다."
    },
    {
        "question": "Perso.ai를 이용하려면 영상 편집 지식이 필요한가요?",
        "answer": "아니요. Perso.ai는 누구나 쉽게 사용할 수 있도록 설계되어 있어, 영상 편집 경험이 없어도 바로 더빙을 시작할 수 있습니다."
    },
    {
        "question": "Perso.ai 고객센터는 어떻게 문의하나요?",
        "answer": "Perso.ai 웹사이트 하단의 '문의하기' 버튼을 통해 이메일 또는 채팅으로 고객센터에 문의할 수 있습니다."
    }
]

@app.on_event("startup")
async def startup_event():
    global embedding_service, vector_store
    print("\n" + "="*60)
    print("🚀 Perso.ai Q&A Chatbot 시작 (Cohere API)")
    print("="*60 + "\n")
    
    try:
        print("1️⃣ Cohere 임베딩 서비스 초기화 중...")
        embedding_service = EmbeddingService()
        
        print("\n2️⃣ 벡터 스토어 초기화 중...")
        vector_store = VectorStore(embedding_service)
        
        print("\n3️⃣ Q&A 데이터 벡터화 시작...")
        vector_store.add_documents(QA_DATA)
        
        print("="*60)
        print("✅ 모든 초기화 완료! 챗봇 서비스 준비됨")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ 초기화 실패: {e}")
        raise

@app.get("/", response_model=HealthResponse)
async def root():
    return {
        "status": "ok",
        "message": "Perso.ai Q&A Chatbot API is running (Cohere Embedding)"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "message": "All systems operational"
    }

@app.post("/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
        
        result = vector_store.get_best_answer(request.question)
        if not result:
            raise HTTPException(status_code=500, detail="검색 중 오류가 발생했습니다.")
        
        return QueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 쿼리 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-search")
async def test_search(q: str = "Perso.ai란?"):
    results = vector_store.search(q, top_k=3)
    return {
        "query": q,
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    print("🌐 서버 시작: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)