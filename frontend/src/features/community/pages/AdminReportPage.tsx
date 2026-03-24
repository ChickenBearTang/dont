import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/shared/hooks';
import {
  getAdminReports,
  getAdminReportDetail,
  processReportBlind,
  processReportReject,
} from '@/features/community/api/adminReportApi';
import type { AdminReportSummaryDto } from '@/features/community/types';
import { ReportProcessModal } from '@/features/community/components/ReportProcessModal';

const FILTER_STATUSES = ['RECEIVED', 'BLINDED', 'REJECTED'] as const;

const AdminReportPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToast();
  const [reports, setReports] = useState<AdminReportSummaryDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [filterStatus, setFilterStatus] = useState<
    'RECEIVED' | 'BLINDED' | 'REJECTED' | undefined
  >(undefined);
  const [processModal, setProcessModal] = useState<{
    isOpen: boolean;
    type: 'blind' | 'reject';
    reportId: number;
    reasonLabel?: string;
    detailText?: string;
  }>({
    isOpen: false,
    type: 'blind',
    reportId: 0,
  });

  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await getAdminReports(filterStatus, currentPage);
      if (response.data) {
        setReports(response.data.content);
        setTotalPages(response.data.totalPages);
      }
    } catch (loadError) {
      console.error('Failed to fetch reports:', loadError);
      error('신고 목록을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReports();
    // Deliberately keyed only to paging/filter state to avoid effect loops from toast object identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filterStatus]);

  const handleViewDetail = async (reportId: number) => {
    try {
      const response = await getAdminReportDetail(reportId);
      if (response.data?.postId) {
        let url = `/community/${response.data.postId}`;
        if (response.data.targetType === 'COMMENT' && response.data.targetId) {
          url += `?commentId=${response.data.targetId}`;
        }
        navigate(url);
        return;
      }

      error('게시물 정보를 찾을 수 없습니다.');
    } catch (detailError) {
      console.error('Failed to fetch report detail:', detailError);
      error('상세 정보를 불러오는 중 오류가 발생했습니다.');
    }
  };

  const handleProcess = async (reportId: number, type: 'blind' | 'reject') => {
    try {
      const response = await getAdminReportDetail(reportId);
      const detail = response.data;
      const reasonLabels: Record<string, string> = {
        SPAM: '스팸/홍보',
        ABUSE: '욕설/비하',
        INAPPROPRIATE: '부적절한 콘텐츠',
        SCAM: '사기/거짓 정보',
        PRIVACY: '개인정보 노출',
        OTHER: '기타',
      };

      setProcessModal({
        isOpen: true,
        type,
        reportId,
        reasonLabel: reasonLabels[detail?.reasonCode || ''] || detail?.reasonCode,
        detailText: detail?.detailText,
      });
    } catch (detailError) {
      console.error('Failed to fetch report detail for processing:', detailError);
      error('상세 정보를 불러오지 못했습니다.');
    }
  };

  const handleModalSubmit = async (note: string) => {
    const { type, reportId } = processModal;
    const actionLabel = type === 'blind' ? '블라인드' : '기각';

    try {
      if (type === 'blind') {
        await processReportBlind(reportId, { processNote: note });
      } else {
        await processReportReject(reportId, { processNote: note });
      }

      success(`${actionLabel} 처리가 완료되었습니다.`);
      await loadReports();
    } catch (submitError) {
      console.error(`Failed to ${type} report:`, submitError);
      error('처리 중 오류가 발생했습니다.');
      throw submitError;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECEIVED':
        return (
          <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
            대기중
          </span>
        );
      case 'BLINDED':
        return (
          <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
            블라인드
          </span>
        );
      case 'REJECTED':
        return (
          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800">
            기각
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            신고 관리 대시보드
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            사용자들이 접수한 신고 내역을 검토하고 처리합니다.
          </p>
        </div>

        <div className="flex gap-2">
          {FILTER_STATUSES.map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => {
                setFilterStatus(filterStatus === status ? undefined : status);
                setCurrentPage(0);
              }}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                filterStatus === status
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {status === 'RECEIVED' ? '대기중' : status === 'BLINDED' ? '블라인드' : '기각'}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
            <tr>
              <th className="px-6 py-4">ID</th>
              <th className="px-6 py-4">유형</th>
              <th className="px-6 py-4">사유</th>
              <th className="px-6 py-4">상태</th>
              <th className="px-6 py-4">접수일</th>
              <th className="px-6 py-4 text-right">관리</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-10 text-center text-gray-400">
                  로딩 중...
                </td>
              </tr>
            ) : reports.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-10 text-center text-gray-400">
                  신고 내역이 없습니다.
                </td>
              </tr>
            ) : (
              reports.map((report) => (
                <tr key={report.reportId} className="transition-colors hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">#{report.reportId}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`text-xs font-semibold ${
                        report.targetType === 'POST' ? 'text-blue-600' : 'text-purple-600'
                      }`}
                    >
                      {report.targetType === 'POST' ? '게시물' : '댓글'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{report.reasonCode}</td>
                  <td className="px-6 py-4">{getStatusBadge(report.reportStatus)}</td>
                  <td className="px-6 py-4 text-xs text-gray-400">
                    {new Date(report.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => void handleViewDetail(report.reportId)}
                        className="rounded-md bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-600 transition-colors hover:bg-blue-100"
                      >
                        상세보기
                      </button>
                      {report.reportStatus === 'RECEIVED' && (
                        <>
                          <button
                            type="button"
                            onClick={() => void handleProcess(report.reportId, 'blind')}
                            className="rounded-md bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 transition-colors hover:bg-red-100"
                          >
                            블라인드
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleProcess(report.reportId, 'reject')}
                            className="rounded-md bg-green-50 px-3 py-1.5 text-xs font-semibold text-green-600 transition-colors hover:bg-green-100"
                          >
                            기각
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50 px-6 py-4">
            <span className="text-xs text-gray-500">
              Page {currentPage + 1} of {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                type="button"
                disabled={currentPage === 0}
                onClick={() => setCurrentPage((prev) => prev - 1)}
                className="rounded border border-gray-200 px-2 py-1 disabled:opacity-30"
              >
                이전
              </button>
              <button
                type="button"
                disabled={currentPage === totalPages - 1}
                onClick={() => setCurrentPage((prev) => prev + 1)}
                className="rounded border border-gray-200 px-2 py-1 disabled:opacity-30"
              >
                다음
              </button>
            </div>
          </div>
        )}
      </div>

      <ReportProcessModal
        isOpen={processModal.isOpen}
        onClose={() => setProcessModal((prev) => ({ ...prev, isOpen: false }))}
        onSubmit={handleModalSubmit}
        type={processModal.type}
        reasonLabel={processModal.reasonLabel}
        detailText={processModal.detailText}
      />
    </div>
  );
};

export default AdminReportPage;
