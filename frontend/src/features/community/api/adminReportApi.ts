import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  AdminReportListResponseDto,
  AdminReportDetailResponseDto,
  ReportProcessRequestDto,
  ReportProcessResponseDto,
} from '@/features/community/types';

export const getAdminReports = async (
  status?: 'RECEIVED' | 'BLINDED' | 'REJECTED',
  page: number = 0,
  size: number = 20
): Promise<ApiResponse<AdminReportListResponseDto>> => {
  return await axiosInstance.get('/admin/reports', {
    params: {
      status,
      page,
      size,
    },
  });
};

export const getAdminReportDetail = async (
  reportId: number
): Promise<ApiResponse<AdminReportDetailResponseDto>> => {
  return await axiosInstance.get(`/admin/reports/${reportId}`);
};

export const processReportBlind = async (
  reportId: number,
  data: ReportProcessRequestDto
): Promise<ApiResponse<ReportProcessResponseDto>> => {
  return await axiosInstance.patch(`/admin/reports/${reportId}/blind`, data);
};

export const processReportReject = async (
  reportId: number,
  data: ReportProcessRequestDto
): Promise<ApiResponse<ReportProcessResponseDto>> => {
  return await axiosInstance.patch(`/admin/reports/${reportId}/reject`, data);
};
