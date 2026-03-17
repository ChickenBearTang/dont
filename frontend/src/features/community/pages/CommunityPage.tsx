import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getPosts } from '../api/communityApi';
import type { BoardCategory, GetPostListResponseDto, PostSummaryDto } from '../types';

const PAGE_SIZE = 12;

export const CommunityPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const category = searchParams.get('category') as BoardCategory | null;
  const pageParam = Number(searchParams.get('page'));
  const currentPage = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;

  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pageInfo, setPageInfo] = useState<GetPostListResponseDto | null>(null);

  const getCategoryName = (cat: BoardCategory | undefined) => {
    switch (cat) {
      case 'FREE':
        return '자유';
      case 'COHORT':
        return '기수';
      case 'PR':
        return 'PR';
      case 'POLL':
        return '토론';
      case 'HOTDEAL':
        return '핫딜';
      default:
        return '전체';
    }
  };

  const getCategoryDot = (cat: BoardCategory | undefined) => {
    switch (cat) {
      case 'FREE':
        return 'bg-blue-400';
      case 'COHORT':
        return 'bg-violet-400';
      case 'PR':
        return 'bg-amber-400';
      case 'POLL':
        return 'bg-emerald-400';
      case 'HOTDEAL':
        return 'bg-rose-400';
      default:
        return 'bg-gray-300';
    }
  };

  const moveToListPage = (targetPage: number) => {
    const params = new URLSearchParams();

    if (category) {
      params.set('category', category);
    }

    if (targetPage > 1) {
      params.set('page', String(targetPage));
    }

    const queryString = params.toString();
    navigate(queryString ? `/community?${queryString}` : '/community');
  };

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true);

      try {
        const res = await getPosts(category, undefined, currentPage - 1, PAGE_SIZE);

        if (res.data) {
          setPosts(res.data.content ?? []);
          setPageInfo(res.data);
        } else {
          setPosts([]);
          setPageInfo(null);
        }
      } catch (error) {
        console.error('Failed to fetch posts:', error);
        setPosts([]);
        setPageInfo(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, [category, currentPage]);

  const categoryTitle = category ? `${getCategoryName(category)} 게시판` : '전체 게시글';

  const cohortGenerationNo =
    category === 'COHORT' && posts.length > 0 ? posts[0].generationNo : null;

  const categoryDescription =
    category === 'COHORT'
      ? cohortGenerationNo
        ? `${cohortGenerationNo}기 게시판입니다. 자유롭게 의견을 나눠보세요.`
        : '기수 게시판입니다. 자유롭게 의견을 나눠보세요.'
      : '우리만의 소식을 나누고 함께 소통해 보세요.';

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

  const totalPages = pageInfo?.totalPages ?? 0;
  const totalElements = pageInfo?.totalElements ?? 0;

  const visiblePageNumbers = useMemo(() => {
    if (totalPages <= 0) return [];

    const maxButtons = 5;
    const half = Math.floor(maxButtons / 2);

    let start = Math.max(1, currentPage - half);
    const end = Math.min(totalPages, start + maxButtons - 1);

    if (end - start + 1 < maxButtons) {
      start = Math.max(1, end - maxButtons + 1);
    }

    return Array.from({ length: end - start + 1 }, (_, idx) => start + idx);
  }, [currentPage, totalPages]);

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">
            {categoryTitle}
          </h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            {categoryDescription}
          </p>
        </div>

        <div className="flex gap-2.5 items-center shrink-0">
          <div className="relative hidden md:block">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-[15px] h-[15px] text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              placeholder="검색"
              className="bg-gray-50 border border-gray-100 text-[13px] rounded-lg pl-9 pr-3 py-2 w-[180px] outline-none focus:border-gray-200 focus:bg-white transition-all font-medium text-gray-600 placeholder:text-gray-300"
            />
          </div>

          <button
            type="button"
            onClick={() =>
              navigate(category ? `/community/write?category=${category}` : '/community/write')
            }
            className="inline-flex items-center gap-2 rounded-xl border border-blue-600 bg-blue-600 px-4 py-2.5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
          >
            <svg
              className="w-4 h-4 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            <span>글쓰기</span>
          </button>
        </div>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 pb-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between py-3">
          <div className="text-[12px] text-gray-400 font-medium">
            총 <span className="font-bold text-gray-700">{totalElements}</span>개
          </div>
          <div className="text-[12px] text-gray-400 font-medium">
            페이지 <span className="font-bold text-gray-700">{currentPage}</span>
            {totalPages > 0 ? ` / ${totalPages}` : ''}
          </div>
        </div>

        <div className="grid grid-cols-12 gap-3 py-3 text-[12px] font-semibold text-gray-300 uppercase tracking-wider items-center border-t border-gray-50">
          <div className="col-span-1">분류</div>
          <div className="col-span-7">제목</div>
          <div className="col-span-2 text-center">작성자</div>
          <div className="col-span-2 text-right pr-1">날짜</div>
        </div>

        <div className="flex flex-col flex-1">
          {loading ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
              <span className="text-[12px] text-gray-300 mt-3 font-medium">불러오는 중</span>
            </div>
          ) : posts.length === 0 ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center mb-3">
                <svg
                  className="w-5 h-5 text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <path
                    d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <p className="font-semibold text-gray-400 text-[13px]">등록된 게시물이 없습니다</p>
              <p className="text-[12px] text-gray-300 mt-1">첫 번째 작성자가 되어보세요</p>
            </div>
          ) : (
            posts.map((post, idx) => (
              <div
                key={post.postId}
                className={`grid grid-cols-12 gap-3 py-3.5 text-[13.5px] items-center hover:bg-gray-50/60 transition-colors cursor-pointer group ${
                  idx !== posts.length - 1 ? 'border-b border-gray-50' : ''
                }`}
              >
                <div className="col-span-1 flex items-center gap-0">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${getCategoryDot(post.category)} flex-shrink-0`}
                  />
                  <span className="text-[12px] text-gray-400 font-medium ml-1.5 hidden lg:inline">
                    {getCategoryName(post.category)}
                  </span>
                </div>

                <div className="col-span-7 flex items-center gap-2 min-w-0">
                  <span className="text-gray-800 font-medium group-hover:text-gray-950 transition-colors truncate">
                    {post.title}
                  </span>
                  {post.commentCount > 0 && (
                    <span className="text-primary-blue text-[11px] font-bold flex-shrink-0 tabular-nums">
                      [{post.commentCount}]
                    </span>
                  )}
                  {post.extra?.poll && !post.extra.poll.isClosed && (
                    <span className="text-[10px] font-bold text-emerald-500 border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 rounded flex-shrink-0 leading-none">
                      투표중
                    </span>
                  )}
                  {post.extra?.pr && post.extra.pr.status === 'OPEN' && (
                    <span className="text-[10px] font-bold text-amber-500 border border-amber-200 bg-amber-50 px-1.5 py-0.5 rounded flex-shrink-0 leading-none">
                      심사중
                    </span>
                  )}
                </div>

                <div className="col-span-2 text-center flex items-center justify-center gap-1.5">
                  <div className="w-5 h-5 rounded-full bg-gray-100 flex-shrink-0 flex items-center justify-center text-[10px] text-gray-400 font-bold">
                    {(post.authorNickname ?? '?').substring(0, 1)}
                  </div>
                  <span className="text-gray-400 font-medium truncate max-w-[70px] text-[12.5px]">
                    {post.authorNickname ?? '알 수 없음'}
                  </span>
                </div>

                <div className="col-span-2 text-right text-gray-300 font-medium text-[12px] pr-1 tabular-nums">
                  {formatDate(post.createdAt)}
                </div>
              </div>
            ))
          )}
        </div>

        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-6">
            <button
              type="button"
              onClick={() => moveToListPage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="inline-flex h-10 items-center justify-center rounded-xl border border-gray-300 bg-white px-4 text-[14px] font-bold text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              이전
            </button>

            <div className="flex items-center gap-1">
              {visiblePageNumbers.map((pageNumber) => {
                const isActive = pageNumber === currentPage;

                return (
                  <button
                    key={pageNumber}
                    type="button"
                    onClick={() => moveToListPage(pageNumber)}
                    className={`inline-flex h-10 min-w-[40px] items-center justify-center rounded-xl border px-3 text-[14px] font-bold shadow-sm transition ${
                      isActive
                        ? 'border-blue-600 bg-blue-600 text-white'
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {pageNumber}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={() => moveToListPage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="inline-flex h-10 items-center justify-center rounded-xl border border-gray-300 bg-white px-4 text-[14px] font-bold text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
