import { create } from 'zustand';
import type { Rapport } from '../types';

interface ReportState {
  reportList: Rapport[];
  setReports: (reports: Rapport[]) => void;
  addReport: (report: Rapport) => void;
  updateReportStatus: (id: string, status: Rapport['statut']) => void;
}

export const useReportStore = create<ReportState>((set) => ({
  reportList: [],
  setReports: (reports) => set({ reportList: reports }),
  addReport: (report) => set((state) => ({ reportList: [report, ...state.reportList] })),
  updateReportStatus: (id, status) =>
    set((state) => ({
      reportList: state.reportList.map((r) => (r.id === id ? { ...r, statut: status } : r)),
    })),
}));
