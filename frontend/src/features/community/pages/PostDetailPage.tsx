import { useEffect, useState, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  createComment,
  deleteComment,
  deletePost,
  getComments,
  getPost,
  toggleReaction,
  updateComment,
} from '../api/communityApi';
import type { BoardCategory, CommentSummaryDto, GetPostResponseDto, ReactionType } from '../types';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

interface CommentNode extends CommentSummaryDto {
  children: CommentNode[];
  isVirtual?: boolean;
}

interface CommentItemProps {
  node: CommentNode;
  depth?: number;
  currentUser: ReturnType<typeof useAuthStore.getState>['user'];
  handleDeleteComment: (id: number) => void;
  postId: string | undefined;
  refreshComments: () => Promise<void>;
  setPost: React.Dispatch<React.SetStateAction<GetPostResponseDto | null>>;
  formatDate: (dateStr: string) => string;
}

const CommentItem = ({
  node,
  depth = 0,
  currentUser,
  handleDeleteComment,
  postId,
  refreshComments,
  setPost,
  formatDate,
}: CommentItemProps) => {
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [submittingReply, setSubmittingReply] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(node.content);
  const [submittingEdit, setSubmittingEdit] = useState(false);

  const commentLikeKey = `comment_like_${node.commentId}`;
  const [isLiked, setIsLiked] = useState(() => localStorage.getItem(commentLikeKey) === 'true');

  const isCommentAuthor = node.isMine ?? currentUser?.userId === node.authorId;

  const handleReplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postId || !replyContent.trim() || submittingReply) return;
    setSubmittingReply(true);
    try {
      await createComment(Number(postId), {
        content: replyContent.trim(),
        parentCommentId: node.commentId,
      });
      setReplyContent('');
      setIsReplying(false);
      await refreshComments();
      setPost((prev) => (prev ? { ...prev, commentCount: prev.commentCount + 1 } : null));
    } catch {
      alert('답글 작성에 실패했습니다.');
    } finally {
      setSubmittingReply(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editContent.trim() || submittingEdit) return;
    setSubmittingEdit(true);
    try {
      await updateComment(node.commentId, { content: editContent.trim() });
      setIsEditing(false);
      await refreshComments();
    } catch {
      alert('댓글 수정에 실패했습니다.');
    } finally {
      setSubmittingEdit(false);
    }
  };

  const handleToggleCommentReaction = async () => {
    if (node.isVirtual) return;
    const nextActive = !isLiked;
    try {
      await toggleReaction({
        targetType: 'COMMENT',
        targetId: node.commentId,
        reactionType: 'LIKE',
        active: nextActive,
      });
      setIsLiked(nextActive);
      if (nextActive) localStorage.setItem(commentLikeKey, 'true');
      else localStorage.removeItem(commentLikeKey);
      await refreshComments();
    } catch (err: unknown) {
      // Handle potential sync issues with older comments
      const axiosError = err as { response?: { status: number } };
      if (axiosError.response?.status === 400 || axiosError.response?.status === 409) {
        // If it failed, it might be already in the target state.
        // Try to force sync the local state and refresh to get the true count.
        setIsLiked(!isLiked);
        if (!isLiked) localStorage.setItem(commentLikeKey, 'true');
        else localStorage.removeItem(commentLikeKey);
        await refreshComments();
      } else {
        alert('반응 처리에 실패했습니다.');
      }
    }
  };

  if (node.isVirtual && node.children.length === 0) return null;

  return (
    <div
      className={`flex flex-col ${depth > 0 ? 'ml-8 mt-4 border-l-2 border-gray-50 pl-4' : 'mt-6 pb-6 border-b border-gray-50 last:border-0'}`}
    >
      <div className="flex gap-3">
        <div className="w-[34px] h-[34px] bg-gray-100 rounded-full shrink-0 flex justify-center items-center font-bold text-gray-400 text-[14px] overflow-hidden">
          {node.isVirtual ? '?' : (node.authorNickname || '?')[0]}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className={`font-bold text-[13.5px] truncate ${node.isVirtual ? 'text-gray-400' : 'text-gray-900'}`}
              >
                {node.isVirtual ? '알 수 없음' : node.authorNickname || '알 수 없음'}
              </span>
              {!node.isVirtual && (
                <span className="text-[12px] text-gray-400 font-medium tracking-tight">
                  {formatDate(node.createdAt)}
                </span>
              )}
            </div>

            {!node.isVirtual && isCommentAuthor && (
              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(!isEditing);
                    setEditContent(node.content);
                  }}
                  className="text-[12px] font-medium text-gray-400 hover:text-gray-700"
                >
                  {isEditing ? '취소' : '수정'}
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteComment(node.commentId)}
                  className="text-[12px] font-medium text-red-400 hover:text-red-600"
                >
                  삭제
                </button>
              </div>
            )}
          </div>

          {isEditing ? (
            <form onSubmit={handleEditSubmit} className="mt-2 flex flex-col gap-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full min-h-[80px] p-3 text-[14px] border border-gray-200 rounded-xl focus:border-blue-500 outline-none resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1.5 text-[12px] font-bold text-gray-500 hover:bg-gray-100 rounded-lg"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={!editContent.trim() || submittingEdit}
                  className="px-3 py-1.5 bg-blue-600 text-white text-[12px] font-bold rounded-lg disabled:bg-gray-300"
                >
                  저장
                </button>
              </div>
            </form>
          ) : (
            <div
              className={`mt-1.5 text-[14px] whitespace-pre-wrap leading-relaxed ${node.isVirtual ? 'text-gray-400 italic' : 'text-gray-800'}`}
            >
              {node.isVirtual ? '삭제된 댓글입니다.' : node.content}
            </div>
          )}

          {!node.isVirtual && (
            <div className="mt-2.5 flex items-center gap-3">
              <button
                onClick={handleToggleCommentReaction}
                className="group flex items-center gap-1.5 transition-colors"
              >
                {isLiked ? (
                  <svg className="w-4 h-4 text-rose-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001z" />
                  </svg>
                ) : (
                  <svg
                    className="w-4 h-4 text-gray-300 group-hover:text-rose-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2.5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                    />
                  </svg>
                )}
                <span
                  className={`text-[12px] font-bold transition-colors ${isLiked ? 'text-rose-600' : 'text-gray-400 group-hover:text-gray-600'}`}
                >
                  {node.likeCount || 0}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setIsReplying(!isReplying)}
                className={`flex items-center gap-1 px-3 py-1 rounded-full text-[12px] font-bold transition-colors ${isReplying ? 'bg-blue-600 text-white' : 'bg-[#EBF5FF] text-[#007AFF] hover:bg-[#D1E9FF]'}`}
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
                <span>답글</span>
              </button>
            </div>
          )}

          {isReplying && (
            <form onSubmit={handleReplySubmit} className="mt-3 flex gap-2">
              <input
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="답글을 입력하세요..."
                className="flex-1 h-9 px-3 rounded-lg bg-gray-50 text-[13px] outline-none border border-gray-100"
              />
              <button
                type="submit"
                disabled={!replyContent.trim() || submittingReply}
                className="px-3 h-9 bg-blue-600 text-white text-[12px] font-bold rounded-lg disabled:bg-gray-300"
              >
                등록
              </button>
            </form>
          )}

          {node.children.length > 0 && (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-[12px] font-bold text-blue-500"
              >
                {isExpanded ? '답글 숨기기' : `답글 ${node.children.length}개 보기`}
              </button>
            </div>
          )}
        </div>
      </div>

      {isExpanded &&
        node.children.map((child) => (
          <CommentItem
            key={child.commentId}
            node={child}
            depth={depth + 1}
            currentUser={currentUser}
            handleDeleteComment={handleDeleteComment}
            postId={postId}
            refreshComments={refreshComments}
            setPost={setPost}
            formatDate={formatDate}
          />
        ))}
    </div>
  );
};

export const PostDetailPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();

  const [post, setPost] = useState<GetPostResponseDto | null>(null);
  const [comments, setComments] = useState<CommentSummaryDto[]>([]);
  const [commentPage, setCommentPage] = useState(0);
  const [hasMoreComments, setHasMoreComments] = useState(false);

  const [commentInput, setCommentInput] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const reactionStorageKey = `post_reaction_${postId}`;
  const [selectedReaction, setSelectedReaction] = useState<ReactionType | null>(() => {
    const saved = localStorage.getItem(reactionStorageKey);
    return saved === 'LIKE' || saved === 'DISLIKE' ? (saved as ReactionType) : null;
  });

  const currentUser = useAuthStore((state) => state.user);

  const isAuthor = useMemo(() => {
    if (!post) return false;
    if (post.isMine) return true;
    return String(currentUser?.userId) === String(post.authorId);
  }, [post, currentUser]);

  const commentTree = useMemo(() => {
    const nodes = new Map<number, CommentNode>();
    const roots: CommentNode[] = [];

    comments.forEach((c) => nodes.set(c.commentId, { ...c, children: [] }));

    comments.forEach((c) => {
      const node = nodes.get(c.commentId)!;
      if (node.parentCommentId === null || node.parentCommentId === undefined) {
        roots.push(node);
      } else {
        const parentId = node.parentCommentId;
        if (!nodes.has(parentId)) {
          const virtualParent: CommentNode = {
            commentId: parentId,
            parentCommentId: null,
            content: '삭제된 댓글입니다.',
            authorId: -1,
            authorNickname: '알 수 없음',
            isMine: false,
            likeCount: 0,
            dislikeCount: 0,
            createdAt: node.createdAt,
            updatedAt: node.createdAt,
            children: [],
            isVirtual: true,
          };
          nodes.set(parentId, virtualParent);
          roots.push(virtualParent);
        }
        nodes.get(parentId)!.children.push(node);
      }
    });

    return roots.sort((a, b) => a.commentId - b.commentId);
  }, [comments]);

  useEffect(() => {
    const fetchPostDetail = async () => {
      if (!postId) return;
      setLoading(true);
      setError(null);
      try {
        const [postRes, commentsRes] = await Promise.all([
          getPost(Number(postId)),
          getComments(Number(postId), 0, 100),
        ]);
        if (postRes.data) {
          setPost(postRes.data);
          setComments(commentsRes.data?.content || []);
          setHasMoreComments(commentsRes.data?.hasNext || false);
          setCommentPage(0);
          const saved = localStorage.getItem(reactionStorageKey);
          setSelectedReaction(
            saved === 'LIKE' || saved === 'DISLIKE' ? (saved as ReactionType) : null
          );
        } else {
          setError('게시글을 찾을 수 없습니다.');
        }
      } catch {
        setError('게시글을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    fetchPostDetail();
  }, [postId, reactionStorageKey]);

  const refreshComments = async () => {
    if (!postId) return;
    const commentsRes = await getComments(Number(postId), 0, 100);
    setComments(commentsRes.data?.content || []);
    setHasMoreComments(commentsRes.data?.hasNext || false);
    setCommentPage(0);
  };

  const handleDelete = async () => {
    if (!postId || !window.confirm('정말 이 게시글을 삭제하시겠습니까?')) return;
    try {
      await deletePost(Number(postId));
      navigate('/community');
    } catch {
      alert('게시글 삭제에 실패했습니다.');
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm('정말 이 댓글을 삭제하시겠습니까?')) return;
    try {
      await deleteComment(commentId);
      await refreshComments();
      setPost((prev) =>
        prev ? { ...prev, commentCount: Math.max(0, prev.commentCount - 1) } : null
      );
    } catch {
      alert('댓글 삭제에 실패했습니다.');
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!postId || !commentInput.trim() || submittingComment) return;
    setSubmittingComment(true);
    try {
      await createComment(Number(postId), { content: commentInput.trim() });
      setCommentInput('');
      await refreshComments();
      setPost((prev) => (prev ? { ...prev, commentCount: prev.commentCount + 1 } : null));
    } catch {
      alert('댓글 작성에 실패했습니다.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const loadMoreComments = async () => {
    if (!postId || !hasMoreComments) return;
    try {
      const nextPage = commentPage + 1;
      const res = await getComments(Number(postId), nextPage, 100);
      if (res.data) {
        setComments((prev) => [...prev, ...(res.data?.content || [])]);
        setHasMoreComments(res.data.hasNext);
        setCommentPage(nextPage);
      }
    } catch {
      // Failed to load more comments
    }
  };

  const handleToggleReaction = async (rType: ReactionType) => {
    if (!postId || !post) return;
    const oppositeType: ReactionType = rType === 'LIKE' ? 'DISLIKE' : 'LIKE';
    const isCurrentActive = selectedReaction === rType;
    const isOppositeActive = selectedReaction === oppositeType;

    try {
      if (!isCurrentActive && isOppositeActive) {
        const resOpp = await toggleReaction({
          targetType: 'POST',
          targetId: Number(postId),
          reactionType: oppositeType,
          active: false,
        });
        if (resOpp.data) {
          setPost((prev) =>
            prev
              ? {
                  ...prev,
                  likeCount: resOpp.data!.likeCount,
                  dislikeCount: resOpp.data!.dislikeCount,
                }
              : null
          );
          setSelectedReaction(null);
        }
      }

      const nextActive = !isCurrentActive;
      const res = await toggleReaction({
        targetType: 'POST',
        targetId: Number(postId),
        reactionType: rType,
        active: nextActive,
      });
      if (res.data) {
        setPost((prev) =>
          prev
            ? { ...prev, likeCount: res.data!.likeCount, dislikeCount: res.data!.dislikeCount }
            : null
        );
        const nextState = res.data!.active ? res.data!.reactionType : null;
        setSelectedReaction(nextState);
        if (nextState) localStorage.setItem(reactionStorageKey, nextState);
        else localStorage.removeItem(reactionStorageKey);
      }
    } catch (error: unknown) {
      const axiosError = error as { response?: { status: number } };
      if (axiosError.response?.status === 409) {
        setSelectedReaction(rType);
        localStorage.setItem(reactionStorageKey, rType);
        const postRes = await getPost(Number(postId));
        if (postRes.data) setPost(postRes.data);
      } else {
        alert('반응 처리에 실패했습니다.');
      }
    }
  };

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
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading)
    return (
      <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden min-h-[600px] flex items-center justify-center p-12">
        <div className="w-8 h-8 border-4 border-gray-100 border-t-blue-500 rounded-full animate-spin mb-4" />
      </div>
    );
  if (error || !post)
    return (
      <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px] items-center justify-center p-12">
        <p className="text-gray-700 font-bold text-[18px] mb-2">
          {error || '게시글을 찾을 수 없습니다.'}
        </p>
        <button
          onClick={() => navigate('/community')}
          className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-sm text-[14px]"
        >
          목록으로 돌아가기
        </button>
      </div>
    );

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col">
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md px-4 h-14 flex items-center justify-between border-b border-gray-100">
        <button
          onClick={() => navigate('/community')}
          className="p-2 -ml-2 text-gray-800 hover:text-black transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="font-bold text-[16px] text-gray-900 tracking-[-0.01em]">
          {getCategoryName(post.category)}
        </span>
        <div className="w-10 flex justify-end">
          {isAuthor ? (
            <div className="relative group">
              <button className="p-2 -mr-2 text-gray-400 hover:text-gray-700">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                  />
                </svg>
              </button>
              <div className="absolute right-0 top-full mt-1 w-28 bg-white border border-gray-100 rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all flex flex-col overflow-hidden">
                <button
                  className="px-4 py-2.5 text-left text-[14px] font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-50"
                  onClick={() => navigate(`/community/${postId}/edit`)}
                >
                  수정
                </button>
                <button
                  className="px-4 py-2.5 text-left text-[14px] font-medium text-red-500 hover:bg-red-50"
                  onClick={handleDelete}
                >
                  삭제
                </button>
              </div>
            </div>
          ) : (
            <div className="w-5" />
          )}
        </div>
      </div>

      <div className="w-full overflow-y-auto">
        <div className="px-5 pt-6 flex items-start gap-3 w-full">
          <div
            className={`w-[42px] h-[42px] rounded-full flex items-center justify-center text-white font-bold text-[18px] shrink-0 ${getCategoryDot(post.category)}`}
          >
            {(post.authorNickname || '?')[0]}
          </div>
          <div className="pt-0.5">
            <div className="text-[15px] font-bold text-gray-900 leading-tight">
              {post.authorNickname || '알 수 없음'}
            </div>
            <div className="text-[12px] text-gray-400 font-medium mt-0.5">
              {formatDate(post.createdAt)}
            </div>
          </div>
        </div>

        <div className="px-5 mt-5">
          <h1 className="text-[20px] font-bold text-gray-900 leading-snug tracking-[-0.01em] whitespace-pre-wrap">
            {post.title}
          </h1>
          <div className="mt-4 text-[16px] text-gray-800 leading-[1.65] font-medium whitespace-pre-wrap word-break-all">
            {post.content}
          </div>
        </div>

        <div className="mt-8 px-5 flex items-center gap-2">
          <button
            onClick={() => handleToggleReaction('LIKE')}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${selectedReaction === 'LIKE' ? 'border border-blue-500 bg-blue-50' : 'border border-gray-200 hover:bg-gray-50'}`}
          >
            <svg
              className={`w-[18px] h-[18px] ${selectedReaction === 'LIKE' ? 'text-blue-600' : 'text-gray-800'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
              />
            </svg>
            <span
              className={`text-[13px] font-medium ${selectedReaction === 'LIKE' ? 'text-blue-700' : 'text-gray-700'}`}
            >
              좋아요 {post.likeCount}
            </span>
          </button>
          <button
            onClick={() => handleToggleReaction('DISLIKE')}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${selectedReaction === 'DISLIKE' ? 'border border-blue-500 bg-blue-50' : 'border border-gray-200 hover:bg-gray-50'}`}
          >
            <svg
              className={`w-[18px] h-[18px] ${selectedReaction === 'DISLIKE' ? 'text-blue-600' : 'text-gray-800'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
              />
            </svg>
            <span
              className={`text-[13px] font-medium ${selectedReaction === 'DISLIKE' ? 'text-blue-700' : 'text-gray-700'}`}
            >
              싫어요 {post.dislikeCount}
            </span>
          </button>
        </div>

        <div className="h-2.5 bg-gray-50 border-y border-gray-100 mt-6 w-full" />

        <div className="px-5 pt-6 pb-24 w-full">
          <h3 className="text-[15px] font-bold text-gray-900 mb-5">{post.commentCount}개의 댓글</h3>
          <div className="flex flex-col">
            {commentTree.length === 0 ? (
              <div className="text-center text-gray-400 text-[14px] py-10 font-medium">
                첫 번째 댓글을 남겨보세요.
              </div>
            ) : (
              commentTree.map((node) => (
                <CommentItem
                  key={node.commentId}
                  node={node}
                  currentUser={currentUser}
                  handleDeleteComment={handleDeleteComment}
                  postId={postId}
                  refreshComments={refreshComments}
                  setPost={setPost}
                  formatDate={formatDate}
                />
              ))
            )}
          </div>
          {hasMoreComments && (
            <button
              type="button"
              onClick={loadMoreComments}
              className="w-full mt-6 py-3 rounded-xl border border-gray-200 text-[14px] font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              댓글 더 보기
            </button>
          )}
        </div>
      </div>

      <form
        onSubmit={handleCommentSubmit}
        className="sticky bottom-0 bg-white border-t border-gray-100 px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <input
            value={commentInput}
            onChange={(e) => setCommentInput(e.target.value)}
            placeholder="댓글을 입력하세요."
            className="flex-1 h-11 px-4 rounded-full bg-gray-100 text-[14px] outline-none placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={submittingComment || !commentInput.trim()}
            className="h-11 px-4 rounded-full bg-blue-600 text-white text-[14px] font-bold disabled:bg-gray-300 transition-colors"
          >
            등록
          </button>
        </div>
      </form>
    </div>
  );
};
