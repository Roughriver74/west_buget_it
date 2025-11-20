import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { ConfigProvider, theme as antdTheme } from 'antd'
import type { ThemeConfig } from 'antd'
import ruRU from 'antd/locale/ru_RU'

type ThemeMode = 'light' | 'dark'
type ComponentSize = 'small' | 'middle' | 'large'

interface ThemeContextType {
  mode: ThemeMode
  toggleTheme: () => void
  setTheme: (mode: ThemeMode) => void
  componentSize: ComponentSize
  setComponentSize: (size: ComponentSize) => void
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
    colorPrimary: '#3b82f6', // Blue-500 - slightly brighter for dark mode
    colorSuccess: '#22c55e', // Green-500
    colorWarning: '#eab308', // Yellow-500
    colorError: '#ef4444', // Red-500
    colorInfo: '#3b82f6',
    fontSize: 14,
    borderRadius: 8,
    colorBgContainer: '#1e293b', // Slate-800 - Lighter than bg for cards
    colorBgLayout: '#0f172a', // Slate-900 - Main background
    colorText: '#f8fafc', // Slate-50
    colorTextSecondary: '#94a3b8', // Slate-400
    colorBorder: '#334155', // Slate-700
    colorBorderSecondary: '#334155',
  },
  components: {
    Layout: {
      bodyBg: '#0f172a', // Slate-900
      headerBg: '#0f172a',
      siderBg: '#020617', // Slate-950 - Darker sidebar
    },
    Menu: {
      darkItemBg: '#020617', // Slate-950
      darkItemSelectedBg: '#1e293b', // Slate-800
      darkItemHoverBg: '#1e293b',
      itemColor: '#94a3b8', // Slate-400
      itemSelectedColor: '#f8fafc', // Slate-50
    },
    Card: {
      colorBgContainer: '#1e293b', // Slate-800
      colorBorderSecondary: '#334155',
    },
    Table: {
      colorBgContainer: '#1e293b', // Slate-800
      headerBg: '#0f172a', // Slate-900 - Darker header for contrast
      headerColor: '#94a3b8', // Slate-400 - Muted header text
      rowHoverBg: '#334155', // Slate-700
      colorBorderSecondary: '#334155',
      borderColor: '#334155',
      headerSplitColor: '#334155',
      bodySortBg: '#0f172a',
    },
    Input: {
      colorBgContainer: '#0f172a', // Slate-900 - Input background
      colorBorder: '#334155',
      colorTextPlaceholder: '#64748b', // Slate-500
      activeBorderColor: '#3b82f6',
    },
    Select: {
      colorBgContainer: '#0f172a',
      colorBorder: '#334155',
      optionSelectedBg: '#334155',
    },
    DatePicker: {
      colorBgContainer: '#0f172a',
      colorBorder: '#334155',
    },
    Modal: {
      contentBg: '#1e293b',
      headerBg: '#1e293b',
    },
    Drawer: {
      colorBgElevated: '#1e293b',
    },
    Dropdown: {
      colorBgElevated: '#1e293b',
    },
    Popover: {
      colorBgElevated: '#1e293b',
    },
  },
}

interface ThemeProviderProps {
  children: ReactNode
}

const THEME_STORAGE_KEY = 'app-theme-mode'
const COMPONENT_SIZE_STORAGE_KEY = 'app-component-size'

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

  const [componentSize, setComponentSize] = useState<ComponentSize>(() => {
    const saved = localStorage.getItem(COMPONENT_SIZE_STORAGE_KEY)
    if (saved === 'small' || saved === 'middle' || saved === 'large') {
      return saved
    }
    return 'middle'
  })

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem(THEME_STORAGE_KEY, mode)

    // Update document root for additional styling if needed
    document.documentElement.setAttribute('data-theme', mode)
    
    // Toggle 'dark' class for Tailwind CSS
    if (mode === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [mode])

  useEffect(() => {
    localStorage.setItem(COMPONENT_SIZE_STORAGE_KEY, componentSize)
  }, [componentSize])

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
    componentSize,
    setComponentSize,
  }

  const currentTheme = mode === 'dark' ? darkTheme : lightTheme

  return (
    <ThemeContext.Provider value={value}>
      <ConfigProvider theme={currentTheme} locale={ruRU} componentSize={componentSize}>
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
