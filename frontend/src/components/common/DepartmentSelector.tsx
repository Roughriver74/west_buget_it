import React from 'react';
import { Select, Spin } from 'antd';
import { BankOutlined } from '@ant-design/icons';
import { useDepartment } from '../../contexts/DepartmentContext';
import { useBreakpoint } from '../../hooks/useBreakpoint';

const DepartmentSelector: React.FC = () => {
  const { departments, selectedDepartment, loading, setSelectedDepartment } = useDepartment();
  const { isMobile } = useBreakpoint();

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
      style={{ width: isMobile ? '100%' : 200 }}
      placeholder="Выберите отдел"
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
