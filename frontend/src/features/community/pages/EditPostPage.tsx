import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import {
  getHotdealDetail,
  getPollDetail,
  getPost,
  updateHotdeal,
  updatePoll,
  updatePost,
} from '../api/communityApi';
import { AttachmentUploader } from '../components/AttachmentUploader';
import { toAttachmentRequests } from '../api/attachmentApi';
import { Card, Button } from '@/shared/components';
import type { BoardCategory, PostAttachmentDto } from '../types';

const getCategoryLabel = (category: BoardCategory | undefined) => {
  switch (category) {
    case 'FREE':
      return '자유 게시판';
    case 'COHORT':
      return '기수 게시판';
    case 'PR':
      return 'PR 게시판';
    case 'POLL':
      return '토론 게시판';
    case 'HOTDEAL':
      return '핫딜 게시판';
    default:
      return '게시글';
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

export const EditPostPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<BoardCategory | undefined>();
  const [attachments, setAttachments] = useState<PostAttachmentDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

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

  const categoryLabel = useMemo(() => getCategoryLabel(category), [category]);
  const isPollCategory = category === 'POLL';
  const isHotdealCategory = category === 'HOTDEAL';

  useEffect(() => {
    const fetchPost = async () => {
      if (!postId) return;
      setLoading(true);

      try {
        const res = await getPost(Number(postId));

        if (!res.data) {
          setErrorMessage('게시글을 찾을 수 없습니다.');
          return;
        }

        setTitle(res.data.title);
        setContent(res.data.content);
        setCategory(res.data.category);
        setAttachments(res.data.attachments ?? []);

        if (res.data.category === 'POLL') {
          const pollRes = await getPollDetail(Number(postId));
          if (pollRes.data) {
            setPollQuestion(pollRes.data.question);
            setPollOptionA(pollRes.data.optionA);
            setPollOptionB(pollRes.data.optionB);
            setPollDeadlineAt(pollRes.data.deadlineAt ? pollRes.data.deadlineAt.slice(0, 16) : '');
          }
        }

        if (res.data.category === 'HOTDEAL') {
          const hotdealRes = await getHotdealDetail(Number(postId));
          if (hotdealRes.data) {
            setProductName(hotdealRes.data.productName);
            setStoreName(hotdealRes.data.storeName ?? '');
            setDealPriceAmount(String(hotdealRes.data.dealPriceAmount ?? ''));
            setOriginalPriceAmount(
              hotdealRes.data.originalPriceAmount != null
                ? String(hotdealRes.data.originalPriceAmount)
                : ''
            );
            setDealUrl(hotdealRes.data.dealUrl ?? '');
            setShippingInfo(hotdealRes.data.shippingInfo ?? '');
            setExpiredAt(hotdealRes.data.expiredAt ? hotdealRes.data.expiredAt.slice(0, 16) : '');
          }
        }
      } catch {
        setErrorMessage('게시글을 불러오지 못했습니다.');
      } finally {
        setLoading(false);
      }
    };

    void fetchPost();
  }, [postId]);

  const handleCancel = () => {
    navigate(`/community/${postId}`);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();

    if (!trimmedTitle) {
      setErrorMessage('제목을 입력해 주세요.');
      return;
    }

    if (!trimmedContent) {
      setErrorMessage('내용을 입력해 주세요.');
      return;
    }

    if (isPollCategory) {
      if (!pollQuestion.trim()) {
        setErrorMessage('질문을 입력해 주세요.');
        return;
      }
      if (!pollOptionA.trim() || !pollOptionB.trim()) {
        setErrorMessage('선택지 A/B를 모두 입력해 주세요.');
        return;
      }
      if (!pollDeadlineAt) {
        setErrorMessage('투표 마감 시각을 선택해 주세요.');
        return;
      }
    }

    if (isHotdealCategory) {
      if (!productName.trim()) {
        setErrorMessage('상품명을 입력해 주세요.');
        return;
      }
      if (!dealPriceAmount || Number(dealPriceAmount) <= 0) {
        setErrorMessage('딜 가격은 1원 이상이어야 합니다.');
        return;
      }
      if (originalPriceAmount && Number(originalPriceAmount) <= 0) {
        setErrorMessage('정가는 1원 이상이어야 합니다.');
        return;
      }
      if (
        originalPriceAmount &&
        Number(dealPriceAmount) > 0 &&
        Number(originalPriceAmount) < Number(dealPriceAmount)
      ) {
        setErrorMessage('정가는 딜 가격보다 크거나 같아야 합니다.');
        return;
      }
      if (dealUrl.trim() && !isValidUrl(dealUrl.trim())) {
        setErrorMessage('딜 링크는 http 또는 https URL이어야 합니다.');
        return;
      }
    }

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      if (isPollCategory) {
        await updatePoll(Number(postId), {
          title: trimmedTitle,
          content: trimmedContent,
          question: pollQuestion.trim(),
          optionA: pollOptionA.trim(),
          optionB: pollOptionB.trim(),
          deadlineAt: pollDeadlineAt,
          attachments: toAttachmentRequests(attachments),
        });
      } else if (isHotdealCategory) {
        await updateHotdeal(Number(postId), {
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
        await updatePost(Number(postId), {
          title: trimmedTitle,
          content: trimmedContent,
          attachments: toAttachmentRequests(attachments),
        });
      }

      navigate(`/community/${postId}`);
    } catch (error: unknown) {
      let serverMessage = '게시글 수정에 실패했습니다. 잠시 후 다시 시도해 주세요.';

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

  if (loading) {
    return (
      <Card className="!p-0 flex flex-col items-center justify-center min-h-[400px] overflow-hidden">
        <div className="flex flex-col items-center gap-3">
          <div className="w-7 h-7 border-2 border-gray-100 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-[13px] text-gray-400 font-medium">게시글을 불러오는 중...</span>
        </div>
      </Card>
    );
  }

  return (
    <Card className="!p-0 flex flex-col min-h-[600px] overflow-hidden">
      <div className="px-7 pt-7 pb-5 border-b border-gray-100 relative w-full z-10">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">게시글 수정</h1>
            <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
              {categoryLabel} 게시글을 수정합니다.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            className="text-[13px] font-bold text-text-subtle hover:text-eel transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="px-7 py-6 flex flex-col gap-6 relative z-10">
        <div className="flex flex-col gap-2">
          <label htmlFor="edit-title" className="text-[13px] font-bold text-gray-700">
            제목
          </label>
          <input
            id="edit-title"
            type="text"
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
          />
          <div className="text-right text-[12px] text-gray-300">{title.length}/200</div>
        </div>

        <AttachmentUploader attachments={attachments} onChange={setAttachments} />

        {isPollCategory ? (
          <>
            <div className="rounded-2xl border border-gray-200 bg-white px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">토론 질문 설정</h2>
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="edit-content" className="text-[13px] font-semibold text-gray-700">
                내용
              </label>
              <textarea
                id="edit-content"
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="min-h-[260px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 resize-none"
              />
            </div>
          </>
        ) : isHotdealCategory ? (
          <>
            <div className="rounded-2xl border border-gray-200 bg-white px-5 py-5">
              <h2 className="text-[16px] font-bold text-gray-900">핫딜 정보</h2>
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
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
                    className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="edit-content" className="text-[13px] font-semibold text-gray-700">
                내용
              </label>
              <textarea
                id="edit-content"
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="min-h-[260px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 resize-none"
              />
            </div>
          </>
        ) : (
          <div className="flex flex-col gap-2">
            <label htmlFor="edit-content" className="text-[13px] font-semibold text-gray-700">
              내용
            </label>
            <textarea
              id="edit-content"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              className="min-h-[320px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 resize-none"
            />
          </div>
        )}

        {errorMessage ? (
          <div className="rounded-xl border border-error-red/20 bg-error-red/5 px-4 py-3 text-[13px] font-bold text-error-red">
            {errorMessage}
          </div>
        ) : null}

        <div className="flex justify-end gap-3 pt-2 shrink-0">
          <Button variant="outline" type="button" onClick={handleCancel} className="!px-5">
            취소
          </Button>
          <Button type="submit" disabled={isSubmitting} className="!px-5">
            {isSubmitting ? '수정 중...' : '수정완료'}
          </Button>
        </div>
      </form>
    </Card>
  );
};
