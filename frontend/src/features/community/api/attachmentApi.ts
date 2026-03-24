import axios from 'axios';
import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  AttachmentPresignFileRequestDto,
  AttachmentPresignResponseDto,
  PostAttachmentDto,
  PostAttachmentRequestDto,
} from '../types';

export const createAttachmentPresignedUrls = async (
  files: AttachmentPresignFileRequestDto[]
): Promise<ApiResponse<AttachmentPresignResponseDto>> => {
  return await axiosInstance.post('/community/attachments/presign', { files });
};

export const uploadCommunityAttachments = async (files: File[]): Promise<PostAttachmentDto[]> => {
  if (files.length === 0) return [];

  const presignResponse = await createAttachmentPresignedUrls(
    files.map((file) => ({
      fileName: file.name,
      contentType: file.type || 'application/octet-stream',
      contentLength: file.size,
    }))
  );

  const presignedFiles = presignResponse.data?.files ?? [];
  if (presignedFiles.length !== files.length) {
    throw new Error('첨부 업로드 URL 발급 결과가 올바르지 않습니다.');
  }

  await Promise.all(
    presignedFiles.map((presignedFile, index) =>
      axios.put(presignedFile.uploadUrl, files[index], {
        headers: presignedFile.headers,
      })
    )
  );

  return presignedFiles.map((presignedFile, index) => ({
    key: presignedFile.key,
    fileName: files[index].name,
    contentType: files[index].type || 'application/octet-stream',
    fileSize: files[index].size,
    fileUrl: presignedFile.fileUrl,
  }));
};

export const toAttachmentRequests = (
  attachments: PostAttachmentDto[]
): PostAttachmentRequestDto[] => {
  return attachments
    .filter((attachment): attachment is PostAttachmentDto & { key: string } => Boolean(attachment.key))
    .map((attachment) => ({
      key: attachment.key,
      fileName: attachment.fileName,
      contentType: attachment.contentType,
      fileSize: attachment.fileSize,
    }));
};
