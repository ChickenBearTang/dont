import { useRef, useState } from 'react';
import { uploadCommunityAttachments } from '../api/attachmentApi';
import type { PostAttachmentDto } from '../types';

interface AttachmentUploaderProps {
  attachments: PostAttachmentDto[];
  onChange: (attachments: PostAttachmentDto[]) => void;
  maxFiles?: number;
  disabled?: boolean;
}

const formatFileSize = (fileSize: number) => {
  if (fileSize >= 1024 * 1024) {
    return `${(fileSize / (1024 * 1024)).toFixed(1)}MB`;
  }
  if (fileSize >= 1024) {
    return `${Math.round(fileSize / 1024)}KB`;
  }
  return `${fileSize}B`;
};

const isImageAttachment = (attachment: PostAttachmentDto) =>
  attachment.contentType.startsWith('image/');

const isPdfAttachment = (attachment: PostAttachmentDto) =>
  attachment.contentType === 'application/pdf';

export const AttachmentUploader = ({
  attachments,
  onChange,
  maxFiles = 5,
  disabled = false,
}: AttachmentUploaderProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSelectFiles = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (selectedFiles.length === 0 || disabled) return;

    if (attachments.length + selectedFiles.length > maxFiles) {
      setError(`첨부는 최대 ${maxFiles}개까지 업로드할 수 있습니다.`);
      event.target.value = '';
      return;
    }

    setError('');
    setUploading(true);
    try {
      const uploadedAttachments = await uploadCommunityAttachments(selectedFiles);
      onChange([...attachments, ...uploadedAttachments]);
    } catch {
      setError('첨부파일 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleRemove = (index: number) => {
    onChange(attachments.filter((_, attachmentIndex) => attachmentIndex !== index));
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-[13px] font-semibold text-gray-700">첨부파일</h3>
          <p className="mt-1 text-[12px] text-gray-400">
            이미지와 PDF를 최대 {maxFiles}개까지 첨부할 수 있습니다.
          </p>
        </div>
        <button
          type="button"
          disabled={disabled || uploading || attachments.length >= maxFiles}
          onClick={() => inputRef.current?.click()}
          className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-[12px] font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {uploading ? '업로드 중...' : '파일 추가'}
        </button>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
        className="hidden"
        onChange={handleSelectFiles}
      />

      {attachments.length > 0 && (
        <div className="rounded-2xl border border-gray-100 bg-gray-50/60">
          {attachments.map((attachment, index) => (
            <div
              key={`${attachment.fileName}-${attachment.fileSize}-${index}`}
              className="flex items-center justify-between gap-4 border-b border-gray-100 px-4 py-4 last:border-0"
            >
              <div className="flex min-w-0 items-center gap-4">
                {isImageAttachment(attachment) ? (
                  <a
                    href={attachment.fileUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="block h-24 w-24 shrink-0 overflow-hidden rounded-2xl border border-gray-200 bg-white"
                  >
                    <img
                      src={attachment.fileUrl}
                      alt={attachment.fileName}
                      className="h-full w-full object-cover"
                    />
                  </a>
                ) : (
                  <a
                    href={attachment.fileUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl border border-gray-200 bg-white"
                  >
                    <div className="text-center">
                      <div className="text-[22px] font-black text-rose-500">
                        {isPdfAttachment(attachment) ? 'PDF' : 'FILE'}
                      </div>
                      <div className="mt-1 text-[11px] font-semibold text-gray-400">열기</div>
                    </div>
                  </a>
                )}

                <div className="min-w-0">
                  <p className="truncate text-[15px] font-semibold text-gray-800">
                    {attachment.fileName}
                  </p>
                  <p className="mt-1 text-[12px] text-gray-400">
                    {attachment.contentType} · {formatFileSize(attachment.fileSize)}
                  </p>
                  <a
                    href={attachment.fileUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex text-[12px] font-semibold text-blue-600 hover:text-blue-700"
                  >
                    새 탭에서 보기
                  </a>
                </div>
              </div>
              <button
                type="button"
                disabled={disabled || uploading}
                onClick={() => handleRemove(index)}
                className="shrink-0 text-[12px] font-semibold text-rose-500 transition hover:text-rose-600 disabled:opacity-50"
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      )}

      {error ? <p className="text-[12px] font-medium text-rose-500">{error}</p> : null}
    </div>
  );
};
