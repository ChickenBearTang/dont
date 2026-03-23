import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { Card, Button } from '@/shared/components';
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
      <Card className="!p-0 flex flex-col items-center justify-center min-h-[400px] overflow-hidden">
        <div className="flex flex-col items-center gap-3">
          <div className="w-7 h-7 border-2 border-primary-blue border-t-transparent rounded-full animate-spin" />
          <span className="text-[13px] text-text-muted font-bold">게시글 불러오는 중...</span>
        </div>
      </Card>
    );
  }

  return (
    <Card className="!p-0 flex flex-col min-h-[600px] overflow-hidden">
      <div className="px-7 pt-7 pb-5 border-b border-gray-100 relative w-full z-10">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-[22px] font-black text-eel tracking-tight">게시글 수정</h1>
            <p className="text-text-muted mt-1 text-[13px] font-bold">
              {categoryLabel}의 게시글을 수정합니다.
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
            placeholder="제목을 입력해 주세요"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 font-bold"
          />
          <div className="text-right text-[12px] text-gray-300">{title.length}/200</div>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="edit-content" className="text-[13px] font-bold text-gray-700">
            내용
          </label>
          <textarea
            id="edit-content"
            placeholder="내용을 입력해 주세요."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[320px] rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-800 outline-none transition focus:border-blue-500 resize-none font-medium leading-relaxed"
          />
        </div>

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
