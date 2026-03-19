import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { createPost } from '../api/communityApi';
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
      return '자유롭게 생각과 정보를 공유해 보세요.';
    case 'COHORT':
      return '내 기수 게시판에 자동으로 글이 등록됩니다.';
    case 'PR':
      return '의견을 묻고 추천을 받는 게시판이에요.';
    case 'POLL':
      return '찬반 의견과 토론 주제를 올릴 수 있어요.';
    case 'HOTDEAL':
      return '좋은 할인 정보와 특가 소식을 공유해 보세요.';
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

  const isCohortCategory = category === 'COHORT';

  const selectedCategoryLabel = useMemo(
    () => CATEGORY_OPTIONS.find((option) => option.value === category)?.label ?? '게시판',
    [category]
  );

  const handleCancel = () => {
    const target = category ? `/community?category=${category}` : '/community';
    navigate(target);
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

    setErrorMessage('');
    setIsSubmitting(true);

    try {
      await createPost({
        category,
        title: trimmedTitle,
        content: trimmedContent,
      });

      navigate(
        category === 'COHORT' ? '/community?category=COHORT' : `/community?category=${category}`
      );
    } catch (error: unknown) {
      console.error('Failed to create post:', error);

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
              게시판을 선택하고 제목과 내용을 입력해 새 글을 등록해 주세요.
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
              내 기수 게시판에 자동으로 등록됩니다.
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
            placeholder="제목을 입력해 주세요"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="h-12 rounded-xl border border-gray-200 bg-white px-4 text-[14px] text-gray-800 outline-none transition focus:border-primary-blue"
          />
          <div className="text-right text-[12px] text-gray-300">{title.length}/200</div>
        </div>

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
            {isSubmitting ? '등록 중...' : '작성완료'}
          </button>
        </div>
      </form>
    </div>
  );
};
