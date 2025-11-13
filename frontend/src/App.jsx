import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// API URL 설정
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: '안녕하세요! Perso.ai에 대해 무엇이든 물어보세요. 😊\n\n벡터 DB 기반으로 정확한 답변만 제공합니다.',
            score: null,
            found: null
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // 자동 스크롤
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // 메시지 전송
    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');

        // 사용자 메시지 추가
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/query`, {
                question: userMessage
            });

            const { answer, score, found } = response.data;

            // 봇 응답 추가
            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: answer,
                    score: score,
                    found: found
                }
            ]);
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: '죄송합니다. 오류가 발생했습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
                    score: null,
                    found: false
                }
            ]);
        } finally {
            setLoading(false);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    // Enter 키로 전송
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // 예시 질문
    const exampleQuestions = [
        "Perso.ai는 어떤 서비스인가요?",
        "어떤 언어를 지원하나요?",
        "요금제는 어떻게 되나요?",
        "회원가입이 필요한가요?"
    ];

    const handleExampleClick = (question) => {
        setInput(question);
        inputRef.current?.focus();
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* 헤더 */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                            <span className="text-white font-bold text-xl">P</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">Perso.ai Q&A</h1>
                            <p className="text-xs text-gray-500">Vector DB 기반 지식 챗봇</p>
                        </div>
                    </div>
                    <div className="text-sm text-gray-500">
                        <span className="inline-flex items-center gap-1.5">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                            온라인
                        </span>
                    </div>
                </div>
            </header>

            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="max-w-4xl mx-auto">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
                        >
                            <div className="flex items-start max-w-[80%] gap-2">
                                {/* 아바타 (Assistant만) */}
                                {msg.role === 'assistant' && (
                                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                        <span className="text-white font-bold text-sm">P</span>
                                    </div>
                                )}

                                {/* 메시지 내용 */}
                                <div className="flex flex-col gap-1">
                                    <div
                                        className={`rounded-2xl px-4 py-3 ${msg.role === 'user'
                                            ? 'bg-blue-600 text-white rounded-br-sm'
                                            : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-sm'
                                            }`}
                                    >
                                        <p className="whitespace-pre-wrap leading-relaxed text-[15px]">
                                            {msg.content}
                                        </p>
                                    </div>

                                    {/* 유사도 정보 */}
                                    {msg.role === 'assistant' && msg.score !== null && msg.score !== undefined && (
                                        <div className="flex items-center gap-2 px-2">
                                            <div className="flex items-center gap-1 text-xs text-gray-500">
                                                <span>유사도: {(msg.score * 100).toFixed(1)}%</span>
                                            </div>

                                            {msg.found && (
                                                <div className="flex items-center gap-1 text-xs text-green-600">
                                                    <span>✓ 정확한 답변</span>
                                                </div>
                                            )}

                                            {msg.found === false && msg.score < 0.7 && (
                                                <div className="flex items-center gap-1 text-xs text-amber-600">
                                                    <span>⚠ 답변 없음</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* 아바타 (User만) */}
                                {msg.role === 'user' && (
                                    <div className="flex-shrink-0 w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                                        <span className="text-white font-bold text-sm">U</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* 로딩 인디케이터 */}
                    {loading && (
                        <div className="flex justify-start mb-4">
                            <div className="flex items-start gap-2 max-w-[80%]">
                                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold text-sm">P</span>
                                </div>
                                <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-gray-100">
                                    <div className="flex gap-1.5">
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* 예시 질문 */}
            {messages.length === 1 && (
                <div className="px-4 pb-4">
                    <div className="max-w-4xl mx-auto">
                        <p className="text-sm text-gray-600 mb-2 font-medium">💡 이런 질문을 해보세요:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {exampleQuestions.map((q, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleExampleClick(q)}
                                    className="text-left px-4 py-3 bg-white border border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm transition-all text-sm text-gray-700"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* 입력 영역 */}
            <div className="border-t border-gray-200 bg-white px-4 py-4 shadow-lg">
                <div className="max-w-4xl mx-auto">
                    <div className="flex gap-2">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Perso.ai에 대해 질문하세요..."
                            disabled={loading}
                            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || loading}
                            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
                        >
                            {loading ? '전송 중...' : '전송'}
                        </button>
                    </div>
                    <p className="text-center text-xs text-gray-500 mt-2">
                        Vector DB 기반 정확한 답변 제공 • 환각(Hallucination) 없음
                    </p>
                </div>
            </div>
        </div>
    );
}

export default App;