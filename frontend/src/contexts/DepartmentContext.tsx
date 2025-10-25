import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import { apiClient } from '../api/client';
import { useAuth } from './AuthContext';

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string | null;
  manager_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface DepartmentContextType {
  departments: Department[];
  selectedDepartment: Department | null;
  loading: boolean;
  setSelectedDepartment: (department: Department | null) => void;
  refreshDepartments: () => Promise<void>;
}

const DepartmentContext = createContext<DepartmentContextType | undefined>(undefined);

export const DepartmentProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDepartment, setSelectedDepartmentState] = useState<Department | null>(null);
  const [loading, setLoading] = useState(false);
  const { token, loading: authLoading } = useAuth();
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  // Load departments function
  const refreshDepartments = async () => {
    // Don't load if no token
    if (!token) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.get('/departments/', {
        params: { is_active: true }
      });

      const depts = response.data;
      setDepartments(depts);

      // Auto-select first department if none selected
      if (depts.length > 0 && !selectedDepartment) {
        const savedDeptId = localStorage.getItem('selectedDepartmentId');
        const savedDept = savedDeptId
          ? depts.find((d: Department) => d.id === parseInt(savedDeptId))
          : null;

        setSelectedDepartmentState(savedDept || depts[0]);
      }
      setHasLoadedOnce(true);
    } catch (error) {
      console.error('Failed to load departments:', error);
      // Don't show error message if it's a 401 (user not authenticated yet)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status !== 401) {
          message.error('Не удалось загрузить список отделов');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  // Load departments when user becomes authenticated
  useEffect(() => {
    if (!authLoading && token && !hasLoadedOnce) {
      console.log('[DepartmentContext] Auth complete, scheduling departments load...');
      // Delay to ensure token is properly set in localStorage and available to interceptor
      const timer = setTimeout(() => {
        console.log('[DepartmentContext] Loading departments now...');
        refreshDepartments();
      }, 300);
      return () => clearTimeout(timer);
    } else if (!token) {
      // Clear departments when logged out
      setDepartments([]);
      setSelectedDepartmentState(null);
      setHasLoadedOnce(false);
    }
  }, [token, authLoading, hasLoadedOnce]);

  const setSelectedDepartment = (department: Department | null) => {
    setSelectedDepartmentState(department);
    if (department) {
      localStorage.setItem('selectedDepartmentId', department.id.toString());
    } else {
      localStorage.removeItem('selectedDepartmentId');
    }
  };

  const value: DepartmentContextType = {
    departments,
    selectedDepartment,
    loading,
    setSelectedDepartment,
    refreshDepartments,
  };

  return <DepartmentContext.Provider value={value}>{children}</DepartmentContext.Provider>;
};

export const useDepartment = () => {
  const context = useContext(DepartmentContext);
  if (context === undefined) {
    throw new Error('useDepartment must be used within a DepartmentProvider');
  }
  return context;
};
