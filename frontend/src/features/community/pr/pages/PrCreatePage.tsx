import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input } from '@/shared/components';
import { createPr } from '@/features/community/pr';
import type { PrCreateRequestPayload } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';

const isValidUrl = (value: string): boolean => {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
};

export const PrCreatePage = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: '',
    content: '',
    itemName: '',
    priceAmount: '',
    category: '',
    purchaseUrl: '',
    imageUrl: '',
    deadlineAt: '',
  });

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const validate = (): string | null => {
    if (!form.title.trim()) return '제목을 입력해주세요.';
    if (!form.content.trim()) return '내용을 입력해주세요.';
    if (!form.itemName.trim()) return '상품명을 입력해주세요.';
    if (!form.priceAmount || Number(form.priceAmount) < 0) {
      return '가격은 0원 이상이어야 합니다.';
    }
    if (form.purchaseUrl.trim() && !isValidUrl(form.purchaseUrl.trim())) {
      return '구매 링크는 http 또는 https URL이어야 합니다.';
    }
    if (form.imageUrl.trim() && !isValidUrl(form.imageUrl.trim())) {
      return '이미지 링크는 http 또는 https URL이어야 합니다.';
    }
    return null;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) return;

    const validationError = validate();
    if (validationError) {
      addToast(validationError, 'error');
      return;
    }

    const payload: PrCreateRequestPayload = {
      title: form.title.trim(),
      content: form.content.trim(),
      itemName: form.itemName.trim(),
      priceAmount: Number(form.priceAmount),
      category: form.category.trim() || undefined,
      purchaseUrl: form.purchaseUrl.trim() || undefined,
      imageUrl: form.imageUrl.trim() || undefined,
      deadlineAt: form.deadlineAt || undefined,
    };

    setIsSubmitting(true);
    try {
      const response = await createPr(payload);
      addToast('PR이 생성되었습니다.', 'success');
      navigate(`/community/pr/${response.data.postId}`, { replace: true });
    } catch {
      addToast('PR 생성에 실패했습니다. 입력값과 서버 상태를 확인해주세요.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-black text-gray-900">PR 생성</h1>
      <p className="text-sm text-gray-500 font-medium mt-1">
        구매 요청 내용을 작성하고 리뷰 투표를 받아보세요.
      </p>

      <form className="mt-4 space-y-2" onSubmit={handleSubmit}>
        <Input
          label="제목"
          name="title"
          value={form.title}
          onChange={handleChange}
          placeholder="예: 로보락 S10 MaxV 구매 요청"
          maxLength={200}
          required
        />
        <Input
          label="상품명"
          name="itemName"
          value={form.itemName}
          onChange={handleChange}
          placeholder="예: 로보락 S10 MaxV Ultra"
          maxLength={200}
          required
        />
        <Input
          label="가격"
          name="priceAmount"
          type="number"
          min={0}
          value={form.priceAmount}
          onChange={handleChange}
          placeholder="예: 1590000"
          required
        />
        <Input
          label="카테고리 (선택)"
          name="category"
          value={form.category}
          onChange={handleChange}
          placeholder="예: 가전"
          maxLength={200}
        />
        <Input
          label="구매 링크 (선택)"
          name="purchaseUrl"
          value={form.purchaseUrl}
          onChange={handleChange}
          placeholder="https://..."
        />
        <Input
          label="이미지 링크 (선택)"
          name="imageUrl"
          value={form.imageUrl}
          onChange={handleChange}
          placeholder="https://..."
          maxLength={255}
        />
        <Input
          label="마감 시각 (선택)"
          name="deadlineAt"
          type="datetime-local"
          value={form.deadlineAt}
          onChange={handleChange}
        />

        <div className="mt-4">
          <label className="font-extrabold text-[15px] text-eel">내용</label>
          <textarea
            name="content"
            value={form.content}
            onChange={handleChange}
            required
            rows={6}
            maxLength={4000}
            className="mt-2 w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel placeholder-[#a0aabf] font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)]"
            placeholder="왜 필요한지, 가격 근거, 대체재 비교를 작성해주세요."
          />
        </div>

        <div className="pt-6">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? '생성 중...' : 'PR 생성'}
          </Button>
        </div>
      </form>
    </Card>
  );
};
