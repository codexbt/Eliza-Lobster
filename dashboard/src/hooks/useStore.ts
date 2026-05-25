import { create } from 'zustand';
import { AgentData } from '../types';

interface StoreState {
  // 3D Camera & Scene
  focusedAgent: string | null;
  setFocusedAgent: (agentName: string | null) => void;
  
  // UI State
  showDetailPanel: boolean;
  setShowDetailPanel: (show: boolean) => void;
  selectedAgentDetails: AgentData | null;
  setSelectedAgentDetails: (agent: AgentData | null) => void;
  
  // Terminal Logs
  terminalLogs: string[];
  addLog: (log: string) => void;
  clearLogs: () => void;
  
  // Effects
  particleEffects: Array<{ id: string; agentName: string; type: string; createdAt: number }>;
  triggerParticleEffect: (agentName: string, effectType: string) => void;
  
  // Settings
  themeMode: 'dark' | 'light';
  setThemeMode: (mode: 'dark' | 'light') => void;
  
  fullscreen: boolean;
  setFullscreen: (fullscreen: boolean) => void;
}

export const useStore = create<StoreState>((set) => ({
  focusedAgent: null,
  setFocusedAgent: (agentName) => set({ focusedAgent: agentName }),
  
  showDetailPanel: false,
  setShowDetailPanel: (show) => set({ showDetailPanel: show }),
  selectedAgentDetails: null,
  setSelectedAgentDetails: (agent) => set({ selectedAgentDetails: agent }),
  
  terminalLogs: ['[SYSTEM] Kairos 3D Dashboard initialized'],
  addLog: (log) =>
    set((state) => ({
      terminalLogs: [...state.terminalLogs.slice(-49), log], // Keep last 50
    })),
  clearLogs: () => set({ terminalLogs: [] }),
  
  particleEffects: [],
  triggerParticleEffect: (agentName, effectType) =>
    set((state) => {
      const newEffect = {
        id: `${agentName}-${effectType}-${Date.now()}`,
        agentName,
        type: effectType,
        createdAt: Date.now(),
      };
      // Remove old effects after 2 seconds
      const filtered = state.particleEffects.filter(
        (e) => Date.now() - e.createdAt < 2000
      );
      return { particleEffects: [...filtered, newEffect] };
    }),
  
  themeMode: 'dark',
  setThemeMode: (mode) => set({ themeMode: mode }),
  
  fullscreen: false,
  setFullscreen: (fullscreen) => set({ fullscreen }),
}));
