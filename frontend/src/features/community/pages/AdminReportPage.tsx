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
import { CommunitySidebar } from '@/features/community/components/CommunitySidebar';

const FILTER_STATUSES = ['RECEIVED', 'BLINDED', 'REJECTED'] as const;

export const REPORT_REASON_LABELS: Record<string, string> = {
  SPAM: '스팸/홍보',
  ABUSE: '욕설/비하',
  INAPPROPRIATE: '부적절한 콘텐츠',
  SCAM: '사기/거짓 정보',
  PRIVACY: '개인정보 노출',
  OTHER: '기타',
};

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
      const response = await getAdminReports(filterStatus, currentPage, 10);
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

      setProcessModal({
        isOpen: true,
        type,
        reportId,
        reasonLabel: REPORT_REASON_LABELS[detail?.reasonCode || ''] || detail?.reasonCode,
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
    <div className="flex gap-6 lg:gap-8 w-full mx-auto items-start max-w-7xl pt-8">
      <aside className="w-[200px] lg:w-[240px] flex-shrink-0 sticky top-[88px]">
        <CommunitySidebar />
      </aside>
      <main className="flex-1 min-w-0">
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
              <button
                type="button"
                onClick={() => {
                  setFilterStatus(undefined);
                  setCurrentPage(0);
                }}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${filterStatus === undefined
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                  }`}
              >
                전체
              </button>
              {FILTER_STATUSES.map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => {
                    setFilterStatus(status);
                    setCurrentPage(0);
                  }}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${filterStatus === status
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
                  <th className="px-6 py-4">관리</th>
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
                    <tr
                      key={report.reportId}
                      className="transition-colors hover:bg-gray-50 cursor-pointer"
                      onClick={() => void handleViewDetail(report.reportId)}
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">#{report.reportId}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`text-xs font-semibold ${report.targetType === 'POST' ? 'text-blue-600' : 'text-purple-600'
                            }`}
                        >
                          {report.targetType === 'POST' ? '게시물' : '댓글'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {REPORT_REASON_LABELS[report.reasonCode] || report.reasonCode}
                      </td>
                      <td className="px-6 py-4">{getStatusBadge(report.reportStatus)}</td>
                      <td className="px-6 py-4 text-xs text-gray-400">
                        {new Date(report.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          {report.reportStatus === 'RECEIVED' && (
                            <>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  void handleProcess(report.reportId, 'blind');
                                }}
                                className="rounded-md bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 transition-colors hover:bg-red-100"
                              >
                                블라인드
                              </button>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  void handleProcess(report.reportId, 'reject');
                                }}
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
              <div className="flex items-center justify-center border-t border-gray-100 bg-white px-6 py-8">
                <div className="flex gap-2 text-sm">
                  <button
                    type="button"
                    disabled={currentPage === 0}
                    onClick={() => setCurrentPage((prev) => prev - 1)}
                    className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 transition-colors hover:bg-gray-50 disabled:opacity-30 disabled:hover:bg-white"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                  </button>

                  {(() => {
                    const maxVisible = 5;
                    let start = Math.max(0, currentPage - 2);
                    let end = Math.min(totalPages - 1, start + maxVisible - 1);
                    if (end - start + 1 < maxVisible) {
                      start = Math.max(0, end - maxVisible + 1);
                    }
                    const pages = [];
                    for (let i = start; i <= end; i++) {
                      pages.push(i);
                    }

                    return pages.map((i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setCurrentPage(i)}
                        className={`flex h-9 w-9 items-center justify-center rounded-lg font-semibold transition-all ${
                          currentPage === i
                            ? 'bg-blue-600 text-white shadow-md border border-blue-600'
                            : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        {i + 1}
                      </button>
                    ));
                  })()}

                  <button
                    type="button"
                    disabled={currentPage === totalPages - 1}
                    onClick={() => setCurrentPage((prev) => prev + 1)}
                    className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 transition-colors hover:bg-gray-50 disabled:opacity-30 disabled:hover:bg-white"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
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
      </main>
    </div>
  );
};

export default AdminReportPage;
