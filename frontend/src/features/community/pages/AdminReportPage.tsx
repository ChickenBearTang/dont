import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import {
  getAdminReports,
  processReportBlind,
  processReportReject,
} from '@/features/community/api/adminReportApi';
import type { AdminReportSummaryDto } from '@/features/community/types';

const AdminReportPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [reports, setReports] = useState<AdminReportSummaryDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [filterStatus, setFilterStatus] = useState<'RECEIVED' | 'BLINDED' | 'REJECTED' | undefined>(
    undefined
  );

  // Robust admin check
  const isAdmin = user?.role?.includes('ADMIN');

  useEffect(() => {
    if (!user || !isAdmin) {
      alert('관리자 권한이 없습니다.');
      navigate('/community');
    }
  }, [user, isAdmin, navigate]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await getAdminReports(filterStatus, currentPage);
      if (res.data) {
        setReports(res.data.content);
        setTotalPages(res.data.totalPages);
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchReports();
    }
  }, [currentPage, filterStatus, isAdmin]);

  const handleProcess = async (reportId: number, type: 'blind' | 'reject') => {
    const note = prompt('처리 사유를 입력하세요 (선택 사항):') || '';
    try {
      if (type === 'blind') {
        await processReportBlind(reportId, { processNote: note });
      } else {
        await processReportReject(reportId, { processNote: note });
      }
      alert('처리가 완료되었습니다.');
      fetchReports();
    } catch (error) {
      console.error('Failed to process report:', error);
      alert('처리 중 오류가 발생했습니다.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECEIVED':
        return (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
            대기중
          </span>
        );
      case 'BLINDED':
        return (
          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
            블라인드
          </span>
        );
      case 'REJECTED':
        return (
          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
            기각됨
          </span>
        );
      default:
        return null;
    }
  };

  if (!user || !isAdmin) return null;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            🚨 신고 관리 시스템
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            사용자들이 접수한 신고 내역을 검토하고 처리합니다.
          </p>
        </div>
        <div className="flex gap-2">
          {(['RECEIVED', 'BLINDED', 'REJECTED'] as const).map((status) => (
            <button
              key={status}
              onClick={() => {
                setFilterStatus(filterStatus === status ? undefined : status);
                setCurrentPage(0);
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterStatus === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {status === 'RECEIVED' ? '대기중' : status === 'BLINDED' ? '블라인드' : '기각됨'}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold">
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
                <tr key={report.reportId} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    #{report.reportId}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`text-xs font-semibold ${report.targetType === 'POST' ? 'text-blue-600' : 'text-purple-600'}`}
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
                        onClick={() => navigate(`/community/post/${report.targetId}`)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="상세보기"
                      >
                        👁️
                      </button>
                      {report.reportStatus === 'RECEIVED' && (
                        <>
                          <button
                            onClick={() => handleProcess(report.reportId, 'blind')}
                            className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                            title="블라인드 처리"
                          >
                            🚫
                          </button>
                          <button
                            onClick={() => handleProcess(report.reportId, 'reject')}
                            className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                            title="기각 처리"
                          >
                            ✅
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
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Page {currentPage + 1} of {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                disabled={currentPage === 0}
                onClick={() => setCurrentPage(currentPage - 1)}
                className="p-1 px-2 rounded border border-gray-200 disabled:opacity-30"
              >
                ◀
              </button>
              <button
                disabled={currentPage === totalPages - 1}
                onClick={() => setCurrentPage(currentPage + 1)}
                className="p-1 px-2 rounded border border-gray-200 disabled:opacity-30"
              >
                ▶
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminReportPage;
