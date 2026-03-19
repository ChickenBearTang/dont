import { useState } from 'react';
import { useDashboardData } from '../../hooks/useDashboardData';
import './Dashboard.css';

import { TopBar } from './TopBar';
import { SummaryPanel } from './SummaryPanel';
import { TrendPanel } from './TrendPanel';
import { CategoryPanel } from './CategoryPanel';
import { RecommendationPanel } from './RecommendationPanel';
import { AiAnalysisPanel } from './AiAnalysisPanel';
import { RankingOverlay } from './RankingOverlay';
import { ChatbotOverlay } from './ChatbotOverlay';

export function Dashboard() {
  const {
    users,
    selectedUser,
    setSelectedUser,
    selectedMonth,
    setSelectedMonth,
    statusMsg,
    dashboardData,
    aiAnalysis,
    recData,
    chatHistory,
    loadStats,
    sendChatMessage
  } = useDashboardData();

  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isRankingOpen, setIsRankingOpen] = useState(false);

  return (
    <div className="dashboard-app">
      <TopBar 
        users={users} 
        selectedUser={selectedUser} 
        setSelectedUser={setSelectedUser} 
        selectedMonth={selectedMonth} 
        setSelectedMonth={setSelectedMonth} 
        onLoad={loadStats} 
        statusMsg={statusMsg} 
      />

      {dashboardData && (
        <>
          <SummaryPanel 
            summary={dashboardData.period_summary} 
            daily={dashboardData.daily_cumulative} 
          />
          <TrendPanel 
            trend={dashboardData.six_month_trend} 
          />
          <CategoryPanel 
            categories={dashboardData.category_breakdown} 
          />
        </>
      )}

      {/* Only show Recommendation & Analysis after data is partially loaded. 
          It triggers separately but we'll show its wrapper and loading state. */}
      {selectedUser && dashboardData && (
        <RecommendationPanel 
          data={recData} 
          onOpenRanking={() => setIsRankingOpen(true)} 
        />
      )}

      {selectedUser && dashboardData && (
        <AiAnalysisPanel 
          analysis={aiAnalysis} 
          periodLabel={`${selectedMonth}`} 
          llmStatusLabel={aiAnalysis ? "ok" : "unknown"} 
        />
      )}

      {/* Overlays */}
      <button className="chat-fab" onClick={() => setIsChatOpen(true)}>💬 해명하기</button>

      {isChatOpen && (
        <ChatbotOverlay 
          isOpen={isChatOpen} 
          onClose={() => setIsChatOpen(false)} 
          chatHistory={chatHistory} 
          onSendMessage={sendChatMessage} 
        />
      )}

      {isRankingOpen && (
        <RankingOverlay 
          isOpen={isRankingOpen} 
          onClose={() => setIsRankingOpen(false)} 
          allCards={recData?.all_cards} 
        />
      )}
    </div>
  );
}
