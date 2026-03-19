import { useState, useRef, useEffect } from 'react';
import type { ChatMessage } from './types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  chatHistory: ChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
}

export function ChatbotOverlay({ isOpen, onClose, chatHistory, onSendMessage }: Props) {
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isOpen]);

  const handleSend = async () => {
    if (!inputText.trim() || isSending) return;
    const text = inputText;
    setInputText("");
    setIsSending(true);
    await onSendMessage(text);
    setIsSending(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSend();
  };

  if (!isOpen) return null;

  return (
    <div className="chat-overlay" style={{ display: 'flex' }}>
      <div className="chat-header">
        <h3 style={{ margin: 0, fontSize: 16 }}>💬 AI 소비 코치에게 해명하기</h3>
        <button 
          onClick={onClose}
          style={{ width: 'auto', padding: '4px 8px', background: 'transparent', color: '#f4f6fb', fontSize: 16, lineHeight: 1 }}
        >
          ✕
        </button>
      </div>
      <div className="chat-messages">
        {chatHistory.map((msg, idx) => (
          <div key={idx} className={`msg ${msg.role === 'user' ? 'user' : 'ai'}`}>
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-area">
        <input 
          type="text" 
          placeholder={isSending ? "AI 코치가 생각 중입니다..." : "예: 친구들 몫도 대신 긁은 거야!"}
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
        />
        <button onClick={handleSend} disabled={isSending}>전송</button>
      </div>
    </div>
  );
}
