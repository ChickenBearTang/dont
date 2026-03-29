import { create } from 'zustand';

interface RankingState {
  isUpdating: boolean;
  setIsUpdating: (val: boolean) => void;
}

export const useRankingStore = create<RankingState>((set) => ({
  isUpdating: false,
  setIsUpdating: (val) => set({ isUpdating: val }),
}));
