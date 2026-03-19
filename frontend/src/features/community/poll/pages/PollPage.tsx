import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPosts } from '@/features/community/api/communityApi';
import type { PostSummaryDto } from '@/features/community/types';

const PAGE_SIZE = 12;

const formatPercent = (value: number) => `${Math.round(value)}%`;

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

export const PollPage = () => {
  const navigate = useNavigate();
  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPolls = async () => {
      setLoading(true);
      setError(null);

      try {
        const res = await getPosts('POLL', undefined, 0, PAGE_SIZE);
        setPosts(res.data?.content ?? []);
      } catch (fetchError) {
        console.error('Failed to fetch poll posts:', fetchError);
        setPosts([]);
        setError('토론 게시글을 불러오지 못했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchPolls();
  }, []);

  const sortedPosts = useMemo(() => {
    return [...posts].sort((a, b) => {
      const aClosed = a.extraSummary?.poll?.isClosed ? 1 : 0;
      const bClosed = b.extraSummary?.poll?.isClosed ? 1 : 0;
      if (aClosed !== bClosed) return aClosed - bClosed;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
  }, [posts]);

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">토론 게시판</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            진행중 토론을 먼저 보여주고, 마감 토론은 아래에 정리합니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/community/write?category=POLL')}
          className="inline-flex items-center gap-2 rounded-xl border border-blue-600 bg-blue-600 px-4 py-2.5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700"
        >
          토론 작성
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
              <p className="font-semibold text-gray-400 text-[13px]">등록된 토론이 없습니다.</p>
            </div>
          ) : (
            sortedPosts.map((post, idx) => {
              const poll = post.extraSummary?.poll;
              const optionACount = poll?.optionACount ?? 0;
              const optionBCount = poll?.optionBCount ?? 0;
              const total = Math.max(1, optionACount + optionBCount);
              const optionARate = (optionACount / total) * 100;
              const optionBRate = (optionBCount / total) * 100;
              const isClosed = poll?.isClosed ?? false;

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
                        isClosed ? 'bg-gray-100 text-gray-500' : 'bg-emerald-50 text-emerald-600'
                      }`}
                    >
                      {isClosed ? '마감' : '진행중'}
                    </span>
                  </div>

                  <p className="mt-1 text-[13px] text-gray-500 line-clamp-1">
                    {poll?.question ?? '토론 질문 미리보기가 없습니다.'}
                  </p>

                  <div className="mt-3 space-y-2">
                    <div>
                      <div className="mb-1 flex items-center justify-between text-[12px] text-gray-500 font-medium">
                        <span className="truncate">{poll?.optionA ?? '선택지 A'}</span>
                        <span>{formatPercent(optionARate)}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-100">
                        <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${optionARate}%` }} />
                      </div>
                    </div>

                    <div>
                      <div className="mb-1 flex items-center justify-between text-[12px] text-gray-500 font-medium">
                        <span className="truncate">{poll?.optionB ?? '선택지 B'}</span>
                        <span>{formatPercent(optionBRate)}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-100">
                        <div className="h-1.5 rounded-full bg-cyan-500" style={{ width: `${optionBRate}%` }} />
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[12px] text-gray-400 font-medium">
                    <span>
                      투표 {poll?.totalVoteCount ?? optionACount + optionBCount} · 마감 {formatDeadline(poll?.deadlineAt)}
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

