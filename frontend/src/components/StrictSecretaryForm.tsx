import React, { useState } from 'react';
import './StrictSecretaryForm.css';

interface StrictSecretaryFormProps {
  onSubmit: (data: { item_text: string; item_link: string; user_reason: string }) => void;
  onClose: () => void;
}

export default function StrictSecretaryForm({ onSubmit, onClose }: StrictSecretaryFormProps) {
  const [itemText, setItemText] = useState('');
  const [itemLink, setItemLink] = useState('');
  const [userReason, setUserReason] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ item_text: itemText, item_link: itemLink, user_reason: userReason });
  };

  return (
    <div
      className="ss-form-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ss-form-title"
    >
      <div className="ss-form-container">
        <button className="ss-close-btn" onClick={onClose} aria-label="닫기">
          &times;
        </button>
        <h2 id="ss-form-title" className="ss-form-title">
          구매 요청서
        </h2>
        <form onSubmit={handleSubmit} className="ss-form">
          <div className="ss-form-group">
            <label htmlFor="buyItem">사고 싶은 물건</label>
            <input
              id="buyItem"
              type="text"
              value={itemText}
              onChange={(e) => setItemText(e.target.value)}
              placeholder="예) 기계식 키보드"
              required
            />
          </div>

          <div className="ss-form-group">
            <label htmlFor="buyLink">링크</label>
            <input
              id="buyLink"
              type="url"
              value={itemLink}
              onChange={(e) => setItemLink(e.target.value)}
              placeholder="https://..."
              required
            />
          </div>

          <div className="ss-form-group">
            <label htmlFor="buyReason">사고 싶은 이유</label>
            <textarea
              id="buyReason"
              value={userReason}
              onChange={(e) => setUserReason(e.target.value)}
              placeholder="이 물건을 사야만 하는 타당한 이유를 적어주세요."
              rows={4}
              required
            />
          </div>

          <button type="submit" className="ss-submit-btn">
            제출하기
          </button>
        </form>
      </div>
    </div>
  );
}
