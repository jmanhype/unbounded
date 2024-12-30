'use client';

import { useEffect, useState } from 'react';
import { CssVarsProvider, useColorScheme } from '@mui/joy/styles';
import CssBaseline from '@mui/joy/CssBaseline';
import { theme } from '../../lib/theme';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return (
    <div suppressHydrationWarning>
      <CssVarsProvider 
        theme={theme} 
        defaultMode="light"
        disableTransitionOnChange
        modeStorageKey="unbounded-color-scheme"
        disableNestedContext
      >
        <CssBaseline />
        {children}
      </CssVarsProvider>
    </div>
  );
} 