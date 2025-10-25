import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRoles }) => {
  const { isAuthenticated, loading, hasRole, user, token } = useAuth();
  const location = useLocation();

  console.log('[ProtectedRoute] Check:', { isAuthenticated, loading, hasUser: !!user, hasToken: !!token, path: location.pathname });

  if (loading) {
    console.log('[ProtectedRoute] Still loading auth...');
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh'
      }}>
        <Spin size="large" tip="Loading..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Not authenticated, redirecting to login');
    // Redirect to login page, but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  console.log('[ProtectedRoute] Authenticated, allowing access');

  // Check if user has required role
  if (requiredRoles && requiredRoles.length > 0) {
    if (!hasRole(requiredRoles)) {
      // User is authenticated but doesn't have required role
      return (
        <Navigate to="/unauthorized" replace />
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
