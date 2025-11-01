import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { ConfigProvider, theme as antdTheme } from 'antd'
import type { ThemeConfig } from 'antd'
import ruRU from 'antd/locale/ru_RU'

type ThemeMode = 'light' | 'dark'

interface ThemeContextType {
  mode: ThemeMode
  toggleTheme: () => void
  setTheme: (mode: ThemeMode) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

// Light theme configuration
const lightTheme: ThemeConfig = {
  algorithm: antdTheme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    fontSize: 14,
    borderRadius: 6,
  },
}

// Dark theme configuration
const darkTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    fontSize: 14,
    borderRadius: 6,
    colorBgContainer: '#1f1f1f',
  },
  components: {
    Layout: {
      bodyBg: '#141414',
      headerBg: '#1f1f1f',
      siderBg: '#141414',
    },
    Menu: {
      darkItemBg: '#141414',
      darkItemSelectedBg: '#1890ff',
      darkItemHoverBg: '#262626',
    },
    Card: {
      colorBgContainer: '#1f1f1f',
      colorBorderSecondary: '#303030',
    },
    Table: {
      colorBgContainer: '#1f1f1f',
      headerBg: '#262626',
      headerColor: '#ffffff',
      rowHoverBg: '#262626',
      colorBorderSecondary: '#303030',
      borderColor: '#303030',
      headerSplitColor: '#303030',
      bodySortBg: '#262626',
      rowSelectedBg: '#1a1a2e',
      rowSelectedHoverBg: '#252540',
    },
    Input: {
      colorBgContainer: '#262626',
      colorBorder: '#303030',
      colorTextPlaceholder: '#8c8c8c',
    },
    Select: {
      colorBgContainer: '#262626',
      colorBorder: '#303030',
    },
    DatePicker: {
      colorBgContainer: '#262626',
      colorBorder: '#303030',
    },
  },
}

interface ThemeProviderProps {
  children: ReactNode
}

const THEME_STORAGE_KEY = 'app-theme-mode'

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  // Initialize theme from localStorage or system preference
  const [mode, setMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(THEME_STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') {
      return saved
    }

    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }

    return 'light'
  })

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem(THEME_STORAGE_KEY, mode)

    // Update document root for additional styling if needed
    document.documentElement.setAttribute('data-theme', mode)
  }, [mode])

  const toggleTheme = () => {
    setMode((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

  const setTheme = (newMode: ThemeMode) => {
    setMode(newMode)
  }

  const value = {
    mode,
    toggleTheme,
    setTheme,
  }

  const currentTheme = mode === 'dark' ? darkTheme : lightTheme

  return (
    <ThemeContext.Provider value={value}>
      <ConfigProvider theme={currentTheme} locale={ruRU}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
