import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  Card,
  Select,
  Space,
  Statistic,
  Row,
  Col,
  Tag,
  Button,
  Dropdown,
  MenuProps,
  message,
} from 'antd';
import {
  DollarOutlined,
  TeamOutlined,
  PlusOutlined,
  DownOutlined,
  DownloadOutlined,
  UploadOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useDepartment } from '../contexts/DepartmentContext';
import { payrollPlanAPI, payrollActualAPI, PayrollPlanWithEmployee, PayrollActualWithEmployee } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import PayrollPlanFormModal from '../components/payroll/PayrollPlanFormModal';
import PayrollActualFormModal from '../components/payroll/PayrollActualFormModal';
import PayrollImportModal from '../components/payroll/PayrollImportModal';
import GeneratePayrollExpensesModal from '../components/payroll/GeneratePayrollExpensesModal';

const { Option } = Select;

const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

export default function PayrollPlanPage() {
  const { selectedDepartment } = useDepartment();
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [planModalVisible, setPlanModalVisible] = useState(false);
  const [actualModalVisible, setActualModalVisible] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [generateExpensesModalVisible, setGenerateExpensesModalVisible] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<number | undefined>();

  // Fetch payroll plans
  const { data: plans = [], isLoading: plansLoading } = useQuery<PayrollPlanWithEmployee[]>({
    queryKey: ['payroll-plans', selectedDepartment?.id, selectedYear],
    queryFn: () =>
      payrollPlanAPI.list({
        department_id: selectedDepartment?.id,
        year: selectedYear,
      }),
  });

  // Fetch payroll actuals
  const { data: actuals = [], isLoading: actualsLoading } = useQuery<PayrollActualWithEmployee[]>({
    queryKey: ['payroll-actuals', selectedDepartment?.id, selectedYear],
    queryFn: () =>
      payrollActualAPI.list({
        department_id: selectedDepartment?.id,
        year: selectedYear,
      }),
  });

  // Group data by month
  const monthlyData = MONTHS.map((monthName, index) => {
    const month = index + 1;
    const monthPlans = plans.filter((p) => p.month === month);
    const monthActuals = actuals.filter((a) => a.month === month);

    const totalPlanned = monthPlans.reduce((sum, p) => sum + Number(p.total_planned), 0);
    const totalPaid = monthActuals.reduce((sum, a) => sum + Number(a.total_paid), 0);
    const variance = totalPaid - totalPlanned;
    const variancePercent = totalPlanned > 0 ? (variance / totalPlanned) * 100 : 0;

    return {
      month,
      monthName,
      employeeCount: monthPlans.length,
      totalPlanned,
      totalPaid,
      variance,
      variancePercent,
    };
  });

  // Calculate year totals
  const yearTotalPlanned = monthlyData.reduce((sum, m) => sum + m.totalPlanned, 0);
  const yearTotalPaid = monthlyData.reduce((sum, m) => sum + m.totalPaid, 0);
  const yearVariance = yearTotalPaid - yearTotalPlanned;

  const handleAddPlan = (month?: number) => {
    setSelectedMonth(month);
    setPlanModalVisible(true);
  };

  const handleAddActual = (month?: number) => {
    setSelectedMonth(month);
    setActualModalVisible(true);
  };

  const handleExportPlans = async () => {
    try {
      await payrollPlanAPI.exportToExcel({
        year: selectedYear,
        department_id: selectedDepartment?.id,
      });
      message.success('Экспорт планов выполнен успешно');
    } catch (error) {
      message.error('Ошибка при экспорте планов');
    }
  };

  const handleExportActuals = async () => {
    try {
      await payrollActualAPI.exportToExcel({
        year: selectedYear,
        department_id: selectedDepartment?.id,
      });
      message.success('Экспорт фактов выполнен успешно');
    } catch (error) {
      message.error('Ошибка при экспорте фактов');
    }
  };

  const addMenuItems: MenuProps['items'] = [
    {
      key: 'plan',
      label: 'Добавить план',
      icon: <PlusOutlined />,
      onClick: () => handleAddPlan(),
    },
    {
      key: 'actual',
      label: 'Добавить факт',
      icon: <PlusOutlined />,
      onClick: () => handleAddActual(),
    },
    {
      type: 'divider',
    },
    {
      key: 'import',
      label: 'Импорт из Excel',
      icon: <UploadOutlined />,
      onClick: () => setImportModalVisible(true),
    },
    {
      type: 'divider',
    },
    {
      key: 'generate-expenses',
      label: 'Создать заявки на ЗП',
      icon: <FileTextOutlined />,
      onClick: () => setGenerateExpensesModalVisible(true),
    },
  ];

  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'export-plans',
      label: 'Экспорт планов',
      onClick: handleExportPlans,
    },
    {
      key: 'export-actuals',
      label: 'Экспорт фактов',
      onClick: handleExportActuals,
    },
  ];

  const columns = [
    {
      title: 'Месяц',
      dataIndex: 'monthName',
      key: 'monthName',
    },
    {
      title: 'Сотрудников',
      dataIndex: 'employeeCount',
      key: 'employeeCount',
    },
    {
      title: 'План (₽)',
      dataIndex: 'totalPlanned',
      key: 'totalPlanned',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Факт (₽)',
      dataIndex: 'totalPaid',
      key: 'totalPaid',
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#3f8600' : undefined }}>
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      title: 'Отклонение (₽)',
      dataIndex: 'variance',
      key: 'variance',
      render: (value: number) => {
        const color = value > 0 ? '#cf1322' : value < 0 ? '#3f8600' : undefined;
        return (
          <span style={{ color }}>
            {value > 0 ? '+' : ''}{formatCurrency(value)}
          </span>
        );
      },
    },
    {
      title: 'Отклонение (%)',
      dataIndex: 'variancePercent',
      key: 'variancePercent',
      render: (value: number) => {
        const color = value > 0 ? '#cf1322' : value < 0 ? '#3f8600' : undefined;
        return (
          <Tag color={color === '#cf1322' ? 'red' : color === '#3f8600' ? 'green' : 'default'}>
            {value > 0 ? '+' : ''}{value.toFixed(2)}%
          </Tag>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>
          <DollarOutlined /> Планирование ФОТ
        </h1>
        <Space>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 150 }}
          >
            {[currentYear - 1, currentYear, currentYear + 1].map((year) => (
              <Option key={year} value={year}>
                {year} год
              </Option>
            ))}
          </Select>
          <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
            <Button icon={<DownloadOutlined />}>
              Экспорт <DownOutlined />
            </Button>
          </Dropdown>
          <Dropdown menu={{ items: addMenuItems }} placement="bottomRight">
            <Button type="primary" icon={<PlusOutlined />}>
              Добавить <DownOutlined />
            </Button>
          </Dropdown>
        </Space>
      </div>

      {/* Year Statistics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего запланировано"
              value={yearTotalPlanned}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего выплачено"
              value={yearTotalPaid}
              precision={2}
              prefix={<TeamOutlined />}
              suffix="₽"
              valueStyle={{ color: yearTotalPaid > 0 ? '#3f8600' : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Отклонение"
              value={yearVariance}
              precision={2}
              suffix="₽"
              valueStyle={{ color: yearVariance > 0 ? '#cf1322' : yearVariance < 0 ? '#3f8600' : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Отклонение (%)"
              value={yearTotalPlanned > 0 ? (yearVariance / yearTotalPlanned) * 100 : 0}
              precision={2}
              suffix="%"
              valueStyle={{
                color:
                  yearVariance > 0
                    ? '#cf1322'
                    : yearVariance < 0
                    ? '#3f8600'
                    : undefined,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Monthly Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={monthlyData}
          rowKey="month"
          loading={plansLoading || actualsLoading}
          pagination={false}
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row style={{ backgroundColor: '#fafafa', fontWeight: 'bold' }}>
                <Table.Summary.Cell index={0}>ИТОГО:</Table.Summary.Cell>
                <Table.Summary.Cell index={1}>
                  {plans.length}
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2}>
                  {formatCurrency(yearTotalPlanned)}
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3}>
                  <span style={{ color: yearTotalPaid > 0 ? '#3f8600' : undefined }}>
                    {formatCurrency(yearTotalPaid)}
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4}>
                  <span style={{
                    color: yearVariance > 0 ? '#cf1322' : yearVariance < 0 ? '#3f8600' : undefined
                  }}>
                    {yearVariance > 0 ? '+' : ''}{formatCurrency(yearVariance)}
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={5}>
                  <Tag color={
                    yearVariance > 0 ? 'red' : yearVariance < 0 ? 'green' : 'default'
                  }>
                    {yearVariance > 0 ? '+' : ''}
                    {yearTotalPlanned > 0 ? ((yearVariance / yearTotalPlanned) * 100).toFixed(2) : '0.00'}%
                  </Tag>
                </Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </Card>

      <PayrollPlanFormModal
        visible={planModalVisible}
        defaultValues={{
          year: selectedYear,
          month: selectedMonth,
        }}
        onCancel={() => {
          setPlanModalVisible(false);
          setSelectedMonth(undefined);
        }}
      />

      <PayrollActualFormModal
        visible={actualModalVisible}
        defaultValues={{
          year: selectedYear,
          month: selectedMonth,
        }}
        onCancel={() => {
          setActualModalVisible(false);
          setSelectedMonth(undefined);
        }}
      />

      <PayrollImportModal
        visible={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
      />

      <GeneratePayrollExpensesModal
        open={generateExpensesModalVisible}
        onClose={() => setGenerateExpensesModalVisible(false)}
      />
    </div>
  );
}
