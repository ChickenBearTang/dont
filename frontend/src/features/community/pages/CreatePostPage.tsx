import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { createHotdealPost, createPollPost, createPost } from '../api/communityApi';
import type { BoardCategory } from '../types';

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
      return '자유롭게 의견과 정보를 공유하는 게시판입니다.';
    case 'COHORT':
      return '내 기수 게시판에 자동으로 등록됩니다.';
    case 'PR':
      return 'PR 관련 글을 공유하는 게시판입니다.';
    case 'POLL':
      return '질문과 선택지를 등록해 투표를 받을 수 있습니다.';
    case 'HOTDEAL':
      return '가격 정보와 마감 정보를 함께 등록하는 게시판입니다.';
    default:
      return '';
  }
};

export const CreatePostPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const initialCategory = searchParams.get('category') as BoardCategory | null;

  const [category, setCategory] = useState<BoardCategory>(initialCategory ?? 'FREE');
  const [title, setTitle] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const [pollQuestion, setPollQuestion] = useState<string>('');
  const [optionA, setOptionA] = useState<string>('');
  const [optionB, setOptionB] = useState<string>('');
  const [deadlineAt, setDeadlineAt] = useState<string>('');

  const [productName, setProductName] = useState<string>('');
  const [storeName, setStoreName] = useState<string>('');
  const [dealPriceAmount, setDealPriceAmount] = useState<string>('');
  const [originalPriceAmount, setOriginalPriceAmount] = useState<string>('');
  const [dealUrl, setDealUrl] = useState<string>('');
  const [shippingInfo, setShippingInfo] = useState<string>('');
  const [expiredAt, setExpiredAt] = useState<string>('');

  const selectedCategoryLabel = useMemo(
    () => CATEGORY_OPTIONS.find((option) => option.value === category)?.label ?? '게시판',
    [category]
  );

  const handleCancel = () => {
    const target = category ? `/community?category=${category}` : '/community';
    navigate(target);
  };

  const handleCategoryChange = (nextCategory: BoardCategory) => {
    setCategory(nextCategory);
    setErrorMessage('');
  };

  const validateCommon = (trimmedTitle: string, trimmedContent: string): boolean => {
    if (!trimmedTitle) {
      setErrorMessage('제목을 입력해 주세요.');
      return false;
    }

    if (!trimmedContent) {
      setErrorMessage('내용을 입력해 주세요.');
      return false;
    }

    return true;
  };

  const submitByCategory = async (trimmedTitle: string, trimmedContent: string) => {
    if (category === 'POLL') {
      const question = pollQuestion.trim();
      const a = optionA.trim();
      const b = optionB.trim();

      if (!question || !a || !b || !deadlineAt) {
        setErrorMessage('토론 질문/선택지/마감일을 모두 입력해 주세요.');
        return;
      }

      await createPollPost({
        title: trimmedTitle,
        content: trimmedContent,
        question,
        optionA: a,
        optionB: b,
        deadlineAt,
      });
      return;
    }

    if (category === 'HOTDEAL') {
      const product = productName.trim();
      const dealPrice = Number(dealPriceAmount);
      const originalPrice = originalPriceAmount ? Number(originalPriceAmount) : undefined;

      if (!product || !Number.isFinite(dealPrice) || dealPrice <= 0) {
        setErrorMessage('상품명과 딜가(1원 이상)는 필수입니다.');
        return;
      }

      await createHotdealPost({
        title: trimmedTitle,
        content: trimmedContent,
        productName: product,
        storeName: storeName.trim() || undefined,
        dealPriceAmount: dealPrice,
        originalPriceAmount:
          originalPrice && Number.isFinite(originalPrice) && originalPrice > 0
            ? originalPrice
            : undefined,
        dealUrl: dealUrl.trim() || undefined,
        shippingInfo: shippingInfo.trim() || undefined,
        expiredAt: expiredAt || undefined,
      });
      return;
    }

    await createPost({
      category,
      title: trimmedTitle,
      content: trimmedContent,
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();
    if (!validateCommon(trimmedTitle, trimmedContent)) return;

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      await submitByCategory(trimmedTitle, trimmedContent);
      navigate(category === 'COHORT' ? '/community?category=COHORT' : `/community?category=${category}`);
    } catch (error: unknown) {
      console.error('Failed to create post:', error);

      let serverMessage = '게시글 작성에 실패했습니다. 잠시 후 다시 시도해 주세요.';
      if (axios.isAxiosError(error)) {
        const responseData = error.response?.data as
          | { message?: string; data?: { message?: string } }
          | undefined;
        serverMessage = responseData?.message ?? responseData?.data?.message ?? serverMessage;
      }
      setErrorMessage(serverMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden min-h-[600px]">
      <div className="px-7 pt-7 pb-5 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">게시글 작성</h1>
            <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
              게시판을 선택하면 필요한 입력 항목이 자동으로 바뀝니다.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            className="text-[13px] font-semibold text-gray-500 hover:text-gray-800 transition-colors"
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
            onChange={(event) => handleCategoryChange(event.target.value as BoardCategory)}
            className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-[12px] text-gray-400">{getCategoryDescription(category)}</p>
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

        {category === 'POLL' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div className="md:col-span-2 flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">투표 질문</label>
              <input
                type="text"
                maxLength={255}
                value={pollQuestion}
                onChange={(event) => setPollQuestion(event.target.value)}
                placeholder="선택지에 대한 질문을 입력해 주세요"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">선택지 A</label>
              <input
                type="text"
                maxLength={255}
                value={optionA}
                onChange={(event) => setOptionA(event.target.value)}
                placeholder="선택지 A"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">선택지 B</label>
              <input
                type="text"
                maxLength={255}
                value={optionB}
                onChange={(event) => setOptionB(event.target.value)}
                placeholder="선택지 B"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>
            <div className="md:col-span-2 flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">마감일시</label>
              <input
                type="datetime-local"
                value={deadlineAt}
                onChange={(event) => setDeadlineAt(event.target.value)}
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>
          </div>
        )}

        {category === 'HOTDEAL' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div className="md:col-span-2 flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">상품명</label>
              <input
                type="text"
                maxLength={200}
                value={productName}
                onChange={(event) => setProductName(event.target.value)}
                placeholder="예: 무선 이어폰 특가"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">스토어명</label>
              <input
                type="text"
                maxLength={100}
                value={storeName}
                onChange={(event) => setStoreName(event.target.value)}
                placeholder="예: 쿠팡"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">배송 정보</label>
              <input
                type="text"
                maxLength={255}
                value={shippingInfo}
                onChange={(event) => setShippingInfo(event.target.value)}
                placeholder="예: 무료배송"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">딜가(원)</label>
              <input
                type="number"
                min={1}
                value={dealPriceAmount}
                onChange={(event) => setDealPriceAmount(event.target.value)}
                placeholder="필수"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">정가(원)</label>
              <input
                type="number"
                min={1}
                value={originalPriceAmount}
                onChange={(event) => setOriginalPriceAmount(event.target.value)}
                placeholder="선택"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="md:col-span-2 flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">상품 URL</label>
              <input
                type="url"
                maxLength={2000}
                value={dealUrl}
                onChange={(event) => setDealUrl(event.target.value)}
                placeholder="https://"
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>

            <div className="md:col-span-2 flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-gray-700">마감일시</label>
              <input
                type="datetime-local"
                value={expiredAt}
                onChange={(event) => setExpiredAt(event.target.value)}
                className="h-11 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
              />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <label htmlFor="content" className="text-[13px] font-semibold text-gray-700">
            내용
          </label>
          <textarea
            id="content"
            placeholder={
              category === 'POLL'
                ? '투표 배경/설명을 입력해 주세요.'
                : `${selectedCategoryLabel}에 등록할 내용을 입력해 주세요.`
            }
            value={content}
            onChange={(event) => setContent(event.target.value)}
            className="min-h-[260px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue resize-none"
          />
        </div>

        {errorMessage ? (
          <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-[13px] font-medium text-red-500">
            {errorMessage}
          </div>
        ) : null}

        <div className="flex justify-end gap-3 pt-2 shrink-0">
          <button
            type="button"
            onClick={handleCancel}
            className="inline-flex h-11 items-center justify-center rounded-xl border border-gray-300 bg-white px-5 text-[14px] font-bold text-gray-700 shadow-sm transition hover:bg-gray-50"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex h-11 items-center justify-center rounded-xl border border-blue-600 bg-blue-600 px-5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700 disabled:cursor-not-allowed disabled:border-gray-300 disabled:bg-gray-300"
          >
            {isSubmitting ? '등록 중..' : '작성 완료'}
          </button>
        </div>
      </form>
    </div>
  );
};
