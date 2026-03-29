import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { createHotdeal, createPoll, createPost } from '../api/communityApi';
import { AttachmentUploader } from '../components/AttachmentUploader';
import { toAttachmentRequests } from '../api/attachmentApi';
import type { BoardCategory, PostAttachmentDto } from '../types';
import { Card, Button } from '@/shared/components';
import { createPr } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';

const CATEGORY_OPTIONS: Array<{ value: BoardCategory; label: string }> = [
  { value: 'FREE', label: '자유 게시판' },
  { value: 'COHORT', label: '기수 게시판' },
  { value: 'PR', label: 'PR 게시판' },
  { value: 'POLL', label: '토론 게시판' },
  { value: 'HOTDEAL', label: '핫딜 게시판' },
];

const getCategoryDescription = (category: BoardCategory) => {
  switch (category) {
    case 'FREE':
      return '자유롭게 생각과 정보를 공유해 보세요.';
    case 'COHORT':
      return '같은 기수 사람들과 더 가까운 이야기를 나눠보세요.';
    case 'PR':
      return '구매 요청을 올리고 다른 사용자의 의견을 받아보세요.';
    case 'POLL':
      return '찬반이 갈리는 주제를 올리고 기한 안에 의견을 모아보세요.';
    case 'HOTDEAL':
      return '좋은 할인 정보를 빠르게 공유해 보세요.';
    default:
      return '';
  }
};

const isValidUrl = (value: string): boolean => {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
};

const buildPrContent = (reason: string, budgetReason: string, alternativeComparison: string) =>
  [
    '왜 필요한가?',
    reason.trim(),
    '',
    '예산은 적절한가?',
    budgetReason.trim(),
    '',
    '대체재는 없는가?',
    alternativeComparison.trim(),
  ].join('\n');

export const CreatePostPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const initialCategory = searchParams.get('category') as BoardCategory | null;

  const [category, setCategory] = useState<BoardCategory>(initialCategory ?? 'FREE');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { addToast } = useUIStore();

  const [itemName, setItemName] = useState('');
  const [priceAmount, setPriceAmount] = useState('');
  const [prCategory, setPrCategory] = useState('');
  const [purchaseUrl, setPurchaseUrl] = useState('');
  const [deadlineAt, setDeadlineAt] = useState('');
  const [reason, setReason] = useState('');
  const [budgetReason, setBudgetReason] = useState('');
  const [alternativeComparison, setAlternativeComparison] = useState('');
  const [attachments, setAttachments] = useState<PostAttachmentDto[]>([]);

  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptionA, setPollOptionA] = useState('');
  const [pollOptionB, setPollOptionB] = useState('');
  const [pollDeadlineAt, setPollDeadlineAt] = useState('');
  const [productName, setProductName] = useState('');
  const [storeName, setStoreName] = useState('');
  const [dealPriceAmount, setDealPriceAmount] = useState('');
  const [originalPriceAmount, setOriginalPriceAmount] = useState('');
  const [dealUrl, setDealUrl] = useState('');
  const [shippingInfo, setShippingInfo] = useState('');
  const [expiredAt, setExpiredAt] = useState('');

  const selectedCategoryLabel = useMemo(
    () => CATEGORY_OPTIONS.find((option) => option.value === category)?.label ?? '게시판',
    [category]
  );

  const isCohortCategory = category === 'COHORT';
  const isPrCategory = category === 'PR';
  const isPollCategory = category === 'POLL';
  const isHotdealCategory = category === 'HOTDEAL';

  const handleCancel = () => {
    const target = category ? `/community?category=${category}` : '/community';
    navigate(target);
  };

  const validateDefaultPost = (trimmedTitle: string, trimmedContent: string) => {
    if (!trimmedTitle) {
      addToast('제목을 입력해 주세요.', 'info');
      return false;
    }
    if (!trimmedContent) {
      addToast('내용을 입력해 주세요.', 'info');
      return false;
    }
    return true;
  };

  const validatePrPost = (trimmedTitle: string) => {
    if (!trimmedTitle) {
      addToast('제목을 입력해 주세요.', 'info');
      return false;
    }
    if (!itemName.trim()) {
      addToast('상품명을 입력해 주세요.', 'info');
      return false;
    }
    if (!priceAmount || Number(priceAmount) < 0) {
      addToast('가격은 0 이상이어야 합니다.', 'info');
      return false;
    }
    if (!reason.trim()) {
      addToast('필요 사유를 입력해 주세요.', 'info');
      return false;
    }
    if (!budgetReason.trim()) {
      addToast('예산 근거를 입력해 주세요.', 'info');
      return false;
    }
    if (!alternativeComparison.trim()) {
      addToast('대체재 비교 내용을 입력해 주세요.', 'info');
      return false;
    }
    if (purchaseUrl.trim() && !isValidUrl(purchaseUrl.trim())) {
      addToast('구매 링크는 http 또는 https URL이어야 합니다.', 'info');
      return false;
    }
    return true;
  };

  const validatePollPost = (trimmedTitle: string, trimmedContent: string) => {
    if (!trimmedTitle) {
      addToast('제목을 입력해 주세요.', 'info');
      return false;
    }
    if (!trimmedContent) {
      addToast('내용을 입력해 주세요.', 'info');
      return false;
    }
    if (!pollQuestion.trim()) {
      addToast('질문을 입력해 주세요.', 'info');
      return false;
    }
    if (!pollOptionA.trim() || !pollOptionB.trim()) {
      addToast('선택지 A/B를 모두 입력해 주세요.', 'info');
      return false;
    }
    if (!pollDeadlineAt) {
      addToast('투표 마감 시각을 선택해 주세요.', 'info');
      return false;
    }
    return true;
  };

  const validateHotdealPost = (trimmedTitle: string, trimmedContent: string) => {
    if (!trimmedTitle) {
      addToast('제목을 입력해 주세요.', 'info');
      return false;
    }
    if (!trimmedContent) {
      addToast('내용을 입력해 주세요.', 'info');
      return false;
    }
    if (!productName.trim()) {
      addToast('상품명을 입력해 주세요.', 'info');
      return false;
    }
    if (!dealPriceAmount || Number(dealPriceAmount) <= 0) {
      addToast('딜 가격은 1원 이상이어야 합니다.', 'info');
      return false;
    }
    if (originalPriceAmount && Number(originalPriceAmount) <= 0) {
      addToast('정가는 1원 이상이어야 합니다.', 'info');
      return false;
    }
    if (
      originalPriceAmount &&
      Number(dealPriceAmount) > 0 &&
      Number(originalPriceAmount) < Number(dealPriceAmount)
    ) {
      addToast('정가는 딜 가격보다 크거나 같아야 합니다.', 'info');
      return false;
    }
    if (dealUrl.trim() && !isValidUrl(dealUrl.trim())) {
      addToast('딜 링크는 http 또는 https URL이어야 합니다.', 'info');
      return false;
    }
    return true;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();

    const isValid = isPrCategory
      ? validatePrPost(trimmedTitle)
      : isPollCategory
        ? validatePollPost(trimmedTitle, trimmedContent)
        : isHotdealCategory
          ? validateHotdealPost(trimmedTitle, trimmedContent)
          : validateDefaultPost(trimmedTitle, trimmedContent);

    if (!isValid) {
      return;
    }

    setIsSubmitting(true);

    try {
      if (isPrCategory) {
        await createPr({
          title: trimmedTitle,
          content: buildPrContent(reason, budgetReason, alternativeComparison),
          itemName: itemName.trim(),
          priceAmount: Number(priceAmount),
          category: prCategory.trim() || undefined,
          purchaseUrl: purchaseUrl.trim() || undefined,
          deadlineAt: deadlineAt || undefined,
          attachments: toAttachmentRequests(attachments),
        });
      } else if (isPollCategory) {
        await createPoll({
          title: trimmedTitle,
          content: trimmedContent,
          question: pollQuestion.trim(),
          optionA: pollOptionA.trim(),
          optionB: pollOptionB.trim(),
          deadlineAt: pollDeadlineAt,
          attachments: toAttachmentRequests(attachments),
        });
      } else if (isHotdealCategory) {
        await createHotdeal({
          title: trimmedTitle,
          content: trimmedContent,
          productName: productName.trim(),
          storeName: storeName.trim() || undefined,
          dealPriceAmount: Number(dealPriceAmount),
          originalPriceAmount: originalPriceAmount ? Number(originalPriceAmount) : undefined,
          dealUrl: dealUrl.trim() || undefined,
          shippingInfo: shippingInfo.trim() || undefined,
          expiredAt: expiredAt || undefined,
          attachments: toAttachmentRequests(attachments),
        });
      } else {
        await createPost({
          category,
          title: trimmedTitle,
          content: trimmedContent,
          attachments: toAttachmentRequests(attachments),
        });
      }

      addToast('게시글이 성공적으로 등록되었습니다.', 'success');
      navigate(`/community?category=${category}`);
    } catch (error: unknown) {
      let serverMessage = '게시글 작성에 실패했습니다. 잠시 후 다시 시도해 주세요.';

      if (axios.isAxiosError(error)) {
        const responseData = error.response?.data as
          | { message?: string; data?: { message?: string } }
          | undefined;

        serverMessage =
          responseData?.message ??
          responseData?.data?.message ??
          '게시글 작성에 실패했습니다. 잠시 후 다시 시도해 주세요.';
      }

      addToast(serverMessage, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="!p-0 flex flex-col min-h-[600px] overflow-hidden">
      <div className="px-7 pt-7 pb-5 border-b border-gray-100 relative z-10 w-full">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">게시글 작성</h1>
            <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
              게시판을 선택하면 입력 폼이 해당 게시판에 맞게 바뀝니다.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            className="text-[13px] font-bold text-text-subtle hover:text-eel transition-colors"
          >
            목록으로 돌아가기
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="px-7 py-6 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <label htmlFor="category" className="text-[13px] font-semibold text-gray-700">
            게시판 선택
          </label>
          <select
            id="category"
            value={category}
            onChange={(event) => setCategory(event.target.value as BoardCategory)}
            className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-[12px] text-gray-400">{getCategoryDescription(category)}</p>

          {isCohortCategory && (
            <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-[13px] font-medium text-blue-700">
              기수 게시판은 현재 로그인한 사용자의 기수로 자동 등록됩니다.
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="title" className="text-[13px] font-semibold text-gray-700">
            제목
          </label>
          <input
            id="title"
            type="text"
            maxLength={200}
            placeholder="제목을 입력해 주세요."
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
          />
          <div className="text-right text-[12px] text-gray-300">{title.length}/200</div>
        </div>

        <AttachmentUploader attachments={attachments} onChange={setAttachments} />

        {isPrCategory ? (
          <>
            <div className="rounded-2xl border border-gray-100 bg-gray-50/70 px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">PR 기본 정보</h2>
              <p className="mt-1 text-[12px] text-gray-400">
                제목은 공통 게시글 제목으로 쓰이고, 아래 필드는 PR 상세 정보로 저장됩니다.
              </p>
              <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <label htmlFor="itemName" className="text-[13px] font-semibold text-gray-700">
                    상품명
                  </label>
                  <input
                    id="itemName"
                    type="text"
                    maxLength={200}
                    value={itemName}
                    onChange={(event) => setItemName(event.target.value)}
                    placeholder="예: 로보락 S10 MaxV Ultra"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="priceAmount" className="text-[13px] font-semibold text-gray-700">
                    가격
                  </label>
                  <input
                    id="priceAmount"
                    type="number"
                    min={0}
                    value={priceAmount}
                    onChange={(event) => setPriceAmount(event.target.value)}
                    placeholder="예: 1590000"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="prCategory" className="text-[13px] font-semibold text-gray-700">
                    상품 카테고리
                  </label>
                  <input
                    id="prCategory"
                    type="text"
                    maxLength={200}
                    value={prCategory}
                    onChange={(event) => setPrCategory(event.target.value)}
                    placeholder="예: 가전"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="deadlineAt" className="text-[13px] font-semibold text-gray-700">
                    투표 마감 시각
                  </label>
                  <input
                    id="deadlineAt"
                    type="datetime-local"
                    value={deadlineAt}
                    onChange={(event) => setDeadlineAt(event.target.value)}
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2 md:col-span-2">
                  <label htmlFor="purchaseUrl" className="text-[13px] font-semibold text-gray-700">
                    구매 링크
                  </label>
                  <input
                    id="purchaseUrl"
                    type="url"
                    value={purchaseUrl}
                    onChange={(event) => setPurchaseUrl(event.target.value)}
                    placeholder="https://..."
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-100 bg-white px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">의사결정에 필요한 내용</h2>
              <p className="mt-1 text-[12px] text-gray-400">
                상세 화면에서 각각의 섹션으로 표시됩니다.
              </p>
              <div className="mt-5 flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <label htmlFor="reason" className="text-[13px] font-semibold text-gray-700">
                    왜 필요한가?
                  </label>
                  <textarea
                    id="reason"
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                    placeholder="구매 배경과 필요성을 적어 주세요."
                    className="min-h-[120px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="budgetReason" className="text-[13px] font-semibold text-gray-700">
                    예산은 적절한가?
                  </label>
                  <textarea
                    id="budgetReason"
                    value={budgetReason}
                    onChange={(event) => setBudgetReason(event.target.value)}
                    placeholder="가격 근거와 예산 판단 이유를 적어 주세요."
                    className="min-h-[120px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label
                    htmlFor="alternativeComparison"
                    className="text-[13px] font-semibold text-gray-700"
                  >
                    대체재는 없는가?
                  </label>
                  <textarea
                    id="alternativeComparison"
                    value={alternativeComparison}
                    onChange={(event) => setAlternativeComparison(event.target.value)}
                    placeholder="대체 상품과 비교한 내용을 적어 주세요."
                    className="min-h-[120px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
                  />
                </div>
              </div>
            </div>
          </>
        ) : isPollCategory ? (
          <>
            <div className="rounded-2xl border border-gray-200 bg-white px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">토론 질문 설정</h2>
              <p className="mt-1 text-[12px] text-gray-500">
                질문, 양자택일 선택지, 마감 시각을 정하면 토론 게시판 카드와 상세 화면에 반영됩니다.
              </p>
              <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2">
                <div className="flex flex-col gap-2 md:col-span-2">
                  <label htmlFor="pollQuestion" className="text-[13px] font-semibold text-gray-700">
                    질문
                  </label>
                  <input
                    id="pollQuestion"
                    type="text"
                    maxLength={255}
                    value={pollQuestion}
                    onChange={(event) => setPollQuestion(event.target.value)}
                    placeholder="예: 로봇청소기를 지금 사는 게 맞을까요?"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="pollOptionA" className="text-[13px] font-semibold text-gray-700">
                    선택지 A
                  </label>
                  <input
                    id="pollOptionA"
                    type="text"
                    maxLength={255}
                    value={pollOptionA}
                    onChange={(event) => setPollOptionA(event.target.value)}
                    placeholder="예: 지금 구매"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="pollOptionB" className="text-[13px] font-semibold text-gray-700">
                    선택지 B
                  </label>
                  <input
                    id="pollOptionB"
                    type="text"
                    maxLength={255}
                    value={pollOptionB}
                    onChange={(event) => setPollOptionB(event.target.value)}
                    placeholder="예: 다음 달까지 보류"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2 md:col-span-2">
                  <label htmlFor="pollDeadlineAt" className="text-[13px] font-semibold text-gray-700">
                    투표 마감 시각
                  </label>
                  <input
                    id="pollDeadlineAt"
                    type="datetime-local"
                    value={pollDeadlineAt}
                    onChange={(event) => setPollDeadlineAt(event.target.value)}
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="content" className="text-[13px] font-semibold text-gray-700">
                내용
              </label>
              <textarea
                id="content"
                placeholder="토론 배경과 판단 근거를 적어 주세요."
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="min-h-[260px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
              />
            </div>
          </>
        ) : isHotdealCategory ? (
          <>
            <div className="rounded-2xl border border-gray-200 bg-white px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">핫딜 정보</h2>
              <p className="mt-1 text-[12px] text-gray-500">
                상품 정보와 가격, 구매 링크를 입력하면 핫딜 카드와 상세 화면에 함께 노출됩니다.
              </p>
              <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2">
                <div className="flex flex-col gap-2 md:col-span-2">
                  <label htmlFor="productName" className="text-[13px] font-semibold text-gray-700">
                    상품명
                  </label>
                  <input
                    id="productName"
                    type="text"
                    maxLength={200}
                    value={productName}
                    onChange={(event) => setProductName(event.target.value)}
                    placeholder="예: 로보락 S10 MaxV Ultra"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="storeName" className="text-[13px] font-semibold text-gray-700">
                    판매처
                  </label>
                  <input
                    id="storeName"
                    type="text"
                    maxLength={100}
                    value={storeName}
                    onChange={(event) => setStoreName(event.target.value)}
                    placeholder="예: 롯데온"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="dealPriceAmount" className="text-[13px] font-semibold text-gray-700">
                    딜 가격
                  </label>
                  <input
                    id="dealPriceAmount"
                    type="number"
                    min={1}
                    value={dealPriceAmount}
                    onChange={(event) => setDealPriceAmount(event.target.value)}
                    placeholder="예: 1590000"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="originalPriceAmount" className="text-[13px] font-semibold text-gray-700">
                    정가
                  </label>
                  <input
                    id="originalPriceAmount"
                    type="number"
                    min={1}
                    value={originalPriceAmount}
                    onChange={(event) => setOriginalPriceAmount(event.target.value)}
                    placeholder="예: 1790000"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="shippingInfo" className="text-[13px] font-semibold text-gray-700">
                    배송 정보
                  </label>
                  <input
                    id="shippingInfo"
                    type="text"
                    maxLength={255}
                    value={shippingInfo}
                    onChange={(event) => setShippingInfo(event.target.value)}
                    placeholder="예: 무료배송"
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor="expiredAt" className="text-[13px] font-semibold text-gray-700">
                    종료 시각
                  </label>
                  <input
                    id="expiredAt"
                    type="datetime-local"
                    value={expiredAt}
                    onChange={(event) => setExpiredAt(event.target.value)}
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
                <div className="flex flex-col gap-2 md:col-span-2">
                  <label htmlFor="dealUrl" className="text-[13px] font-semibold text-gray-700">
                    딜 링크
                  </label>
                  <input
                    id="dealUrl"
                    type="url"
                    value={dealUrl}
                    onChange={(event) => setDealUrl(event.target.value)}
                    placeholder="https://..."
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="content" className="text-[13px] font-semibold text-gray-700">
                내용
              </label>
              <textarea
                id="content"
                placeholder="핫딜의 특징, 구매 포인트, 주의할 점을 적어 주세요."
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="min-h-[260px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
              />
            </div>
          </>
        ) : (
          <div className="flex flex-col gap-2">
            <label htmlFor="content" className="text-[13px] font-semibold text-gray-700">
              내용
            </label>
            <textarea
              id="content"
              placeholder={`${selectedCategoryLabel}에 등록할 내용을 입력해 주세요.`}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              className="min-h-[320px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
            />
          </div>
        )}


        <div className="flex justify-end gap-3 pt-2 shrink-0">
          <Button variant="outline" type="button" onClick={handleCancel} className="!px-5">
            취소
          </Button>
          <Button type="submit" disabled={isSubmitting} className="!px-5">
            {isSubmitting ? '등록 중...' : '작성완료'}
          </Button>
        </div>
      </form>
    </Card>
  );
};