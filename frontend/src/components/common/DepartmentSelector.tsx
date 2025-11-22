import React, { useState, useEffect } from 'react'
import { Select, Spin } from 'antd';
import { BankOutlined } from '@ant-design/icons';
import { useDepartment } from '../../contexts/DepartmentContext';

const DepartmentSelector: React.FC = () => {
  const { departments, selectedDepartment, loading, setSelectedDepartment } = useDepartment();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (loading) {
    return <Spin size="small" />;
  }

  if (departments.length === 0) {
    return null;
  }

  return (
    <Select
      value={selectedDepartment?.id}
      onChange={(value) => {
        const dept = departments.find(d => d.id === value);
        setSelectedDepartment(dept || null);
      }}
      style={{ width: isMobile ? 120 : 200, minWidth: isMobile ? 100 : 150 }}
      placeholder={isMobile ? 'Отдел' : 'Выберите отдел'}
      suffixIcon={<BankOutlined />}
    >
      {departments.map(dept => (
        <Select.Option key={dept.id} value={dept.id}>
          {dept.name}
        </Select.Option>
      ))}
    </Select>
  );
};

export default DepartmentSelector;
