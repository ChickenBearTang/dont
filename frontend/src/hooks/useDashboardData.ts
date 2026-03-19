import { useState, useEffect, useCallback } from 'react';
import type { User, DashboardPayload, RecommendationPayload, ChatMessage } from '../components/Dashboard/types';

export function useDashboardData() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [selectedMonth, setSelectedMonth] = useState<string>('2026-02');
  
  const [statusMsg, setStatusMsg] = useState<string>('월간 소비 통계를 불러올 준비가 되었습니다.');
  const [loading, setLoading] = useState<boolean>(false);
  
  const [dashboardData, setDashboardData] = useState<DashboardPayload | null>(null);
  const [recData, setRecData] = useState<RecommendationPayload | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<DashboardPayload['ai_analysis'] | null>(null);
  
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    { role: 'ai', text: '무엇이든 변명해보세요! 억울한 지출이나 큰 돈을 쓴 이유가 타당하다면 리포트에 스티커를 붙여드릴게요. 😉' }
  ]);

  // Load Users
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch('/api/v1/users');
        const data = await res.json();
        setUsers(data.users || []);
        if (data.users && data.users.length > 0) {
          setSelectedUser(data.users[0].name);
        }
      } catch (err) {
        setStatusMsg('유저 목록을 불러오지 못했습니다.');
      }
    };
    fetchUsers();
  }, []);

  // Initial load when user list populates
  useEffect(() => {
    if (selectedUser) {
      loadStats();
    }
  }, [selectedUser]); // Removed full loadStats dependency to avoid infinite loops, but we can trigger explicitly via button

  const loadStats = useCallback(async () => {
    if (!selectedUser) return;
    setStatusMsg('통계를 불러오는 중입니다...');
    setLoading(true);
    
    try {
      const statsParams = new URLSearchParams({ user_name: selectedUser, month: selectedMonth });
      const aiParams = new URLSearchParams({
        user_name: selectedUser,
        start: selectedMonth,
        end: selectedMonth,
        include_ai: "true"
      });

      const [statsRes, aiRes, recRes] = await Promise.all([
        fetch(`/api/v1/mock-consumption-stats?${statsParams.toString()}`),
        fetch(`/api/v1/consumption-report?${aiParams.toString()}`),
        fetch(`/api/v1/recommendation?${statsParams.toString()}`)
      ]);

      if (!statsRes.ok) throw new Error((await statsRes.json()).detail || "통계를 불러오지 못했습니다.");
      if (!aiRes.ok) throw new Error((await aiRes.json()).detail || "AI 분석을 불러오지 못했습니다.");
      
      const statsPayload = await statsRes.json();
      const aiPayload = await aiRes.json();
      const recPayload = await recRes.json();

      setDashboardData(statsPayload);
      setAiAnalysis(aiPayload.ai_analysis);
      setRecData(recPayload);
      
      const [, month] = statsPayload.meta.selected_month.split('-');
      setStatusMsg(`${statsPayload.meta.user_name} · ${Number(month)}월 통계를 불러왔습니다.`);
      
      // Reset Chat History when loading a new month/user
      setChatHistory([
        { role: 'ai', text: '무엇이든 변명해보세요! 억울한 지출이나 큰 돈을 쓴 이유가 타당하다면 리포트에 스티커를 붙여드릴게요. 😉' }
      ]);
    } catch (err: any) {
      setStatusMsg(err.message);
      setAiAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, [selectedUser, selectedMonth]);

  const sendChatMessage = async (text: string) => {
    if (!text.trim()) return;
    
    const newChat = [...chatHistory, { role: 'user', text } as ChatMessage];
    setChatHistory(newChat);

    try {
      const apiHistory = newChat.filter(msg => msg.role !== 'ai').map(msg => ({ role: msg.role === 'user' ? 'user' : 'model', text: msg.text }));
      
      const res = await fetch('/api/v1/chat', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: selectedUser,
          month: selectedMonth,
          message: text,
          history: apiHistory.slice(0, -1) // Excluding the one we just added to build history
        })
      });

      if (!res.ok) throw new Error("챗봇 응답 오류");
      const result = await res.json();
      
      const updatedChat = [...newChat, { role: 'ai', text: result.response } as ChatMessage];
      setChatHistory(updatedChat);

      if (result.is_valid) {
        setChatHistory(prev => [...prev, { role: 'ai', text: "✨ 해명 접수 완료! 분석 리포트를 다시 갱신할게요." }]);
        setStatusMsg("새로운 해명을 바탕으로 리포트를 재생성합니다...");
        
        const aiParams = new URLSearchParams({
          user_name: selectedUser,
          start: selectedMonth,
          end: selectedMonth,
          include_ai: "true"
        });
        const aiResponse = await fetch(`/api/v1/consumption-report?${aiParams.toString()}`);
        if (aiResponse.ok) {
          const aiPayload = await aiResponse.json();
          setAiAnalysis(aiPayload.ai_analysis);
          const [, mo] = selectedMonth.split('-');
          setStatusMsg(`${selectedUser} · ${Number(mo)}월 통계 및 해명 기반 새 분석을 불러왔습니다.`);
        }
      }
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', text: "앗, 코치팀과 연결이 끊어졌어요. 다시 시도해주세요." }]);
    }
  };

  return {
    users,
    selectedUser,
    setSelectedUser,
    selectedMonth,
    setSelectedMonth,
    statusMsg,
    loading,
    dashboardData,
    aiAnalysis,
    recData,
    chatHistory,
    loadStats,
    sendChatMessage
  };
}
