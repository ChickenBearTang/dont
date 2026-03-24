import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input } from '@/shared/components';
import { createPr } from '@/features/community/pr';
import type { PrCreateRequestPayload } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';
import { AttachmentUploader } from '@/features/community/components/AttachmentUploader';
import { toAttachmentRequests } from '@/features/community/api/attachmentApi';
import type { PostAttachmentDto } from '@/features/community/types';

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
    itemName: '',
    priceAmount: '',
    category: '',
    purchaseUrl: '',
    deadlineAt: '',
    reason: '',
    budgetReason: '',
    alternativeComparison: '',
  });
  const [attachments, setAttachments] = useState<PostAttachmentDto[]>([]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const validate = (): string | null => {
    if (!form.title.trim()) return '제목을 입력해주세요.';
    if (!form.itemName.trim()) return '상품명을 입력해주세요.';
    if (!form.priceAmount || Number(form.priceAmount) < 0) {
      return '가격은 0원 이상이어야 합니다.';
    }
    if (!form.reason.trim()) return '왜 필요한지 입력해주세요.';
    if (!form.budgetReason.trim()) return '예산 근거를 입력해주세요.';
    if (!form.alternativeComparison.trim()) return '대체재 비교 내용을 입력해주세요.';
    if (form.purchaseUrl.trim() && !isValidUrl(form.purchaseUrl.trim())) {
      return '구매 링크는 http 또는 https URL이어야 합니다.';
    }
    return null;
  };

  const buildContent = () =>
    [
      '왜 필요한가?',
      form.reason.trim(),
      '',
      '예산은 적절한가?',
      form.budgetReason.trim(),
      '',
      '대체재는 없는가?',
      form.alternativeComparison.trim(),
    ].join('\n');

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
      content: buildContent(),
      itemName: form.itemName.trim(),
      priceAmount: Number(form.priceAmount),
      category: form.category.trim() || undefined,
      purchaseUrl: form.purchaseUrl.trim() || undefined,
      deadlineAt: form.deadlineAt || undefined,
      attachments: toAttachmentRequests(attachments),
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
    <Card className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-black text-gray-900">구매 PR 생성</h1>
      <p className="text-sm text-gray-500 font-medium mt-1">
        다른 사용자의 의견을 참고하되, 최종 결정은 작성자가 직접 내리는 구매 요청입니다.
      </p>

      <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-black text-gray-900">기본 정보</h2>
            <p className="text-sm text-gray-500">목록과 상세 상단에 노출될 공통 정보입니다.</p>
          </div>
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
            label="마감 시각 (선택)"
            name="deadlineAt"
            type="datetime-local"
            value={form.deadlineAt}
            onChange={handleChange}
          />
          <AttachmentUploader attachments={attachments} onChange={setAttachments} />
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-black text-gray-900">의사결정에 필요한 내용</h2>
            <p className="text-sm text-gray-500">
              아래 세 항목은 상세 화면에서 각각의 섹션으로 표시됩니다.
            </p>
          </div>

          <div>
            <label className="font-extrabold text-[15px] text-eel">왜 필요한가?</label>
            <textarea
              name="reason"
              value={form.reason}
              onChange={handleChange}
              required
              rows={5}
              maxLength={4000}
              className="mt-2 w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel placeholder-[#a0aabf] font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)]"
              placeholder="구매 배경과 필요성을 적어주세요."
            />
          </div>

          <div>
            <label className="font-extrabold text-[15px] text-eel">예산은 적절한가?</label>
            <textarea
              name="budgetReason"
              value={form.budgetReason}
              onChange={handleChange}
              required
              rows={5}
              maxLength={4000}
              className="mt-2 w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel placeholder-[#a0aabf] font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)]"
              placeholder="가격 근거와 예산 판단 이유를 적어주세요."
            />
          </div>

          <div>
            <label className="font-extrabold text-[15px] text-eel">대체재는 없는가?</label>
            <textarea
              name="alternativeComparison"
              value={form.alternativeComparison}
              onChange={handleChange}
              required
              rows={5}
              maxLength={4000}
              className="mt-2 w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel placeholder-[#a0aabf] font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)]"
              placeholder="대체 상품과 비교한 내용을 적어주세요."
            />
          </div>
        </section>

        <div className="pt-2">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? '생성 중...' : 'PR 생성'}
          </Button>
        </div>
      </form>
    </Card>
  );
};
