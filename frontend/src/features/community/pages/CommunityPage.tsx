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
        return '?먯쑀';
      case 'COHORT':
        return '湲곗닔';
      case 'PR':
        return 'PR';
      case 'POLL':
        return '?좊줎';
      case 'HOTDEAL':
        return '?ル뵜';
      default:
        return '?꾩껜';
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

  const categoryTitle = category ? `${getCategoryName(category)} 寃뚯떆?? : '?꾩껜 寃뚯떆湲';

  const cohortGenerationNo =
    category === 'COHORT' && posts.length > 0 ? posts[0].generationNo : null;

  const categoryDescription =
    category === 'COHORT'
      ? cohortGenerationNo
        ? `${cohortGenerationNo}湲?寃뚯떆?먯엯?덈떎. ?먯쑀濡?쾶 ?섍껄???섎닠蹂댁꽭??`
        : '湲곗닔 寃뚯떆?먯엯?덈떎. ?먯쑀濡?쾶 ?섍껄???섎닠蹂댁꽭??'
      : '?곕━留뚯쓽 ?뚯떇???섎늻怨??④퍡 ?뚰넻??蹂댁꽭??';

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMs / 3600000);

    if (diffMin < 1) return '諛⑷툑';
    if (diffMin < 60) return `${diffMin}遺???;
    if (diffHour < 24) return `${diffHour}?쒓컙 ??;

    return date.toLocaleDateString('ko-KR', {
      month: 'numeric',
      day: 'numeric',
    });
  };

  const toWon = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

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
              placeholder="寃??
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
            <span>湲?곌린</span>
          </button>
        </div>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 pb-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between py-3">
          <div className="text-[12px] text-gray-400 font-medium">
            珥?<span className="font-bold text-gray-700">{totalElements}</span>媛?          </div>
          <div className="text-[12px] text-gray-400 font-medium">
            ?섏씠吏 <span className="font-bold text-gray-700">{currentPage}</span>
            {totalPages > 0 ? ` / ${totalPages}` : ''}
          </div>
        </div>

        {category !== ''HOTDEAL'' && (
          <div className="grid grid-cols-12 gap-3 py-3 text-[12px] font-semibold text-gray-300 uppercase tracking-wider items-center border-t border-gray-50">
            <div className="col-span-1">遺꾨쪟</div>
            <div className="col-span-7">?쒕ぉ</div>
            <div className="col-span-2 text-center">?묒꽦??/div>
            <div className="col-span-2 text-right pr-1">?좎쭨</div>
          </div>
        )}

        <div className="flex flex-col flex-1">
          {loading ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
              <span className="text-[12px] text-gray-300 mt-3 font-medium">遺덈윭?ㅻ뒗 以?/span>
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
              <p className="font-semibold text-gray-400 text-[13px]">?깅줉??寃뚯떆臾쇱씠 ?놁뒿?덈떎</p>
              <p className="text-[12px] text-gray-300 mt-1">泥?踰덉㎏ ?묒꽦?먭? ?섏뼱蹂댁꽭??/p>
            </div>
          ) : (
            posts.map((post, idx) => (
              <div
                key={post.postId}
                onClick={() => navigate(`/community/${post.postId}`)}
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
                  <span className="truncate text-gray-800 font-medium group-hover:text-gray-900">
                    {post.title}
                  </span>

                  {post.commentCount > 0 && (
                    <span className="text-[12px] font-semibold text-blue-500 shrink-0">
                      [{post.commentCount}]
                    </span>
                  )}

                  {post.extraSummary?.poll && !post.extraSummary.poll.isClosed && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-500 font-semibold shrink-0">
                      吏꾪뻾以?                    </span>
                  )}

                  {post.extraSummary?.pr && post.extraSummary.pr.status === 'OPEN' && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-500 font-semibold shrink-0">
                      ?ы몴以?                    </span>
                  )}
                </div>

                <div className="col-span-2 text-center text-gray-500 text-[13px] font-medium truncate">
                  {post.authorNickname || '?????놁쓬'}
                </div>

                <div className="col-span-2 text-right text-gray-400 text-[12px] font-medium">
                  {formatDate(post.createdAt)}
                </div>
              </div>
            ))
          )}
        </div>

        {!loading && totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-1.5">
            <button
              type="button"
              onClick={() => moveToListPage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-2 rounded-lg border border-gray-100 text-[13px] font-medium text-gray-500 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              ?댁쟾
            </button>

            {visiblePageNumbers.map((pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                onClick={() => moveToListPage(pageNumber)}
                className={`min-w-[36px] h-[36px] rounded-lg text-[13px] font-semibold transition ${
                  pageNumber === currentPage
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-500 hover:bg-gray-50'
                }`}
              >
                {pageNumber}
              </button>
            ))}

            <button
              type="button"
              onClick={() => moveToListPage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-2 rounded-lg border border-gray-100 text-[13px] font-medium text-gray-500 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              ?ㅼ쓬
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

