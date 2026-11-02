import { create } from 'zustand';

interface ConfigState {
  apiUrl: string;
  setApiUrl: (url: string) => void;
}

export const useConfigStore = create<ConfigState>((set) => {
  let initialApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  if (typeof window !== 'undefined') {
    localStorage.removeItem('api_key');
    const savedUrl = localStorage.getItem('api_url');
    if (savedUrl) initialApiUrl = savedUrl;
  }

  return {
    apiUrl: initialApiUrl,
    setApiUrl: (url) => {
      set({ apiUrl: url });
      if (typeof window !== 'undefined') {
        localStorage.setItem('api_url', url);
      }
    },
  };
});
