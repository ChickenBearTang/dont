import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPosts } from '@/features/community/api/communityApi';
import type { PostSummaryDto } from '@/features/community/types';

const PAGE_SIZE = 12;

const toWon = (value: number) =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const getDiscountRate = (originalPrice: number, dealPrice: number) => {
  if (!originalPrice || originalPrice <= 0) {
    return 0;
  }
  return Math.max(0, Math.round(((originalPrice - dealPrice) / originalPrice) * 100));
};

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return '방금';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;

  return date.toLocaleDateString('ko-KR', {
    month: 'numeric',
    day: 'numeric',
  });
};

const formatDeadline = (dateStr?: string) => {
  if (!dateStr) return '-';
  const parsed = new Date(dateStr);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};

export const HotdealPage = () => {
  const navigate = useNavigate();
  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHotdeals = async () => {
      setLoading(true);
      setError(null);

      try {
        const res = await getPosts('HOTDEAL', undefined, 0, PAGE_SIZE);
        setPosts(res.data?.content ?? []);
      } catch (fetchError) {
        console.error('Failed to fetch hotdeal posts:', fetchError);
        setPosts([]);
        setError('핫딜 게시글을 불러오지 못했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchHotdeals();
  }, []);

  const sortedPosts = useMemo(() => {
    return [...posts].sort((a, b) => {
      const aExpired = a.extraSummary?.hotdeal?.isExpired ? 1 : 0;
      const bExpired = b.extraSummary?.hotdeal?.isExpired ? 1 : 0;
      if (aExpired !== bExpired) return aExpired - bExpired;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
  }, [posts]);

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">핫딜 게시판</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            진행중 딜을 먼저 보여주고, 마감 딜은 아래에 정리합니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/community/write?category=HOTDEAL')}
          className="inline-flex items-center gap-2 rounded-xl border border-blue-600 bg-blue-600 px-4 py-2.5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700"
        >
          핫딜 작성
        </button>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 pb-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between py-3">
          <div className="text-[12px] text-gray-400 font-medium">
            총 <span className="font-bold text-gray-700">{sortedPosts.length}</span>건
          </div>
        </div>

        <div className="flex flex-col flex-1">
          {loading ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
              <span className="text-[12px] text-gray-300 mt-3 font-medium">불러오는 중...</span>
            </div>
          ) : error ? (
            <div className="py-20 text-center text-[13px] font-medium text-red-500">{error}</div>
          ) : sortedPosts.length === 0 ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <p className="font-semibold text-gray-400 text-[13px]">등록된 핫딜이 없습니다.</p>
            </div>
          ) : (
            sortedPosts.map((post, idx) => {
              const hotdeal = post.extraSummary?.hotdeal;
              const dealPrice = hotdeal?.dealPriceAmount ?? 0;
              const originalPrice = hotdeal?.originalPriceAmount ?? 0;
              const discountRate = getDiscountRate(originalPrice, dealPrice);
              const isExpired = hotdeal?.isExpired ?? false;

              return (
                <div
                  key={post.postId}
                  onClick={() => navigate(`/community/${post.postId}`)}
                  className={`py-4 cursor-pointer group ${idx !== sortedPosts.length - 1 ? 'border-b border-gray-50' : ''}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-[15px] font-semibold text-gray-900 group-hover:text-black truncate">
                      {post.title}
                    </h2>
                    <span
                      className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-bold ${
                        isExpired ? 'bg-gray-100 text-gray-500' : 'bg-rose-50 text-rose-600'
                      }`}
                    >
                      {isExpired ? '마감' : `${discountRate}% 할인`}
                    </span>
                  </div>

                  <div className="mt-2 flex items-end gap-2">
                    <strong className="text-[18px] font-bold text-gray-900">{toWon(dealPrice)}</strong>
                    {originalPrice > 0 && (
                      <span className="text-[13px] font-medium text-gray-400 line-through">{toWon(originalPrice)}</span>
                    )}
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[12px] text-gray-400 font-medium">
                    <span>
                      {hotdeal?.storeName ?? '-'} · 마감 {formatDeadline(hotdeal?.expiredAt)}
                    </span>
                    <span>{formatDate(post.createdAt)}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

