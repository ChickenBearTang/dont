import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { getPost, updatePost } from '../api/communityApi';
import type { BoardCategory } from '../types';

const getCategoryLabel = (cat: BoardCategory | undefined) => {
  switch (cat) {
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
      return '게시판';
  }
};

export const EditPostPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<BoardCategory | undefined>();
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const categoryLabel = useMemo(() => getCategoryLabel(category), [category]);

  useEffect(() => {
    const fetchPost = async () => {
      if (!postId) return;
      setLoading(true);

      try {
        const res = await getPost(Number(postId));

        if (res.data) {
          setTitle(res.data.title);
          setContent(res.data.content);
          setCategory(res.data.category);
        } else {
          setErrorMessage('게시글을 찾을 수 없습니다.');
        }
      } catch {
        setErrorMessage('게시글을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [postId]);

  const handleCancel = () => {
    navigate(`/community/${postId}`);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

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

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      await updatePost(Number(postId), {
        title: trimmedTitle,
        content: trimmedContent,
      });

      navigate(`/community/${postId}`);
    } catch (error: unknown) {
      console.error('Failed to update post:', error);

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
      <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-7 h-7 border-2 border-gray-100 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-[13px] text-gray-400 font-medium">게시글 불러오는 중...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden min-h-[600px]">
      <div className="px-7 pt-7 pb-5 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">게시글 수정</h1>
            <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
              {categoryLabel}의 게시글을 수정합니다.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            className="text-[13px] font-semibold text-gray-500 hover:text-gray-800 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="px-7 py-6 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <label htmlFor="edit-title" className="text-[13px] font-semibold text-gray-700">
            제목
          </label>
          <input
            id="edit-title"
            type="text"
            maxLength={200}
            placeholder="제목을 입력해 주세요"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500"
          />
          <div className="text-right text-[12px] text-gray-300">{title.length}/200</div>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="edit-content" className="text-[13px] font-semibold text-gray-700">
            내용
          </label>
          <textarea
            id="edit-content"
            placeholder="내용을 입력해 주세요."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[320px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 resize-none"
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
            {isSubmitting ? '수정 중...' : '수정완료'}
          </button>
        </div>
      </form>
    </div>
  );
};
