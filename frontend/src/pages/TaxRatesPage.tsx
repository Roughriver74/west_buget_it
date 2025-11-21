import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Switch,
  Tag,
  Tooltip,
  message} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  SafetyOutlined,
  SettingOutlined} from '@ant-design/icons';
import dayjs from 'dayjs';

import { ResponsiveTable } from '@/components/common/ResponsiveTable';
import { taxRateAPI, TaxRateListItem, TaxType } from '../api/taxRates';

const TAX_TYPE_LABELS: Record<TaxType, string> = {
  INCOME_TAX: 'НДФЛ',
  PENSION_FUND: 'ПФР',
  MEDICAL_INSURANCE: 'ФОМС',
  SOCIAL_INSURANCE: 'ФСС',
  INJURY_INSURANCE: 'НС/ПЗ'};

const TAX_TYPE_COLORS: Record<TaxType, string> = {
  INCOME_TAX: 'volcano',
  PENSION_FUND: 'geekblue',
  MEDICAL_INSURANCE: 'purple',
  SOCIAL_INSURANCE: 'gold',
  INJURY_INSURANCE: 'cyan'};

const rateToPercent = (value?: number | null) =>
  value !== undefined && value !== null ? `${(value * 100).toFixed(2)}%` : '—';

export default function TaxRatesPage() {
  const [filters, setFilters] = useState<{
    taxType?: TaxType;
    isActive?: boolean;
    effectiveDate?: string;
  }>({});
  const [isModalOpen, setModalOpen] = useState(false);
  const [editingRate, setEditingRate] = useState<TaxRateListItem | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const {
    data: taxRates = [],
    isLoading,
    isFetching} = useQuery({
    queryKey: ['tax-rates', filters],
    queryFn: () =>
      taxRateAPI.list({
        tax_type: filters.taxType,
        is_active: filters.isActive,
        effective_date: filters.effectiveDate})});

  const createMutation = useMutation({
    mutationFn: (values: any) =>
      taxRateAPI.create({
        ...values,
        effective_from: values.effective_from.format('YYYY-MM-DD'),
        effective_to: values.effective_to ? values.effective_to.format('YYYY-MM-DD') : null}),
    onSuccess: () => {
      message.success('Ставка добавлена');
      queryClient.invalidateQueries({ queryKey: ['tax-rates'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось сохранить ставку');
    }});

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      taxRateAPI.update(id, {
        ...values,
        effective_from: values.effective_from.format('YYYY-MM-DD'),
        effective_to: values.effective_to ? values.effective_to.format('YYYY-MM-DD') : null}),
    onSuccess: () => {
      message.success('Ставка обновлена');
      queryClient.invalidateQueries({ queryKey: ['tax-rates'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось обновить ставку');
    }});

  const deleteMutation = useMutation({
    mutationFn: (id: number) => taxRateAPI.remove(id),
    onSuccess: () => {
      message.success('Ставка удалена');
      queryClient.invalidateQueries({ queryKey: ['tax-rates'] });
    },
    onError: () => {
      message.error('Не удалось удалить ставку');
    }});

  const initMutation = useMutation({
    mutationFn: () => taxRateAPI.initializeDefault(),
    onSuccess: ({ count }) => {
      message.success(`Добавлено ${count} ставок по умолчанию`);
      queryClient.invalidateQueries({ queryKey: ['tax-rates'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось инициализировать ставки');
    }});

  const handleModalOpen = (record?: TaxRateListItem) => {
    setEditingRate(record || null);
    setModalOpen(true);
    if (record) {
      form.setFieldsValue({
        tax_type: record.tax_type,
        name: record.name,
        description: record.description,
        rate: Number(record.rate),
        threshold_amount: record.threshold_amount,
        rate_above_threshold: record.rate_above_threshold,
        effective_from: dayjs(record.effective_from),
        effective_to: record.effective_to ? dayjs(record.effective_to) : null,
        is_active: record.is_active,
        notes: record.notes});
    } else {
      form.resetFields();
      form.setFieldsValue({
        tax_type: 'INCOME_TAX',
        rate: 0.13,
        effective_from: dayjs(),
        is_active: true});
    }
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setEditingRate(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingRate) {
        updateMutation.mutate({ id: editingRate.id, values });
      } else {
        createMutation.mutate(values);
      }
    } catch {
      // validation handled by antd
    }
  };

  const columns = [
    {
      title: 'Тип',
      dataIndex: 'tax_type',
      key: 'tax_type',
      render: (value: TaxType) => (
        <Tag color={TAX_TYPE_COLORS[value]}>{TAX_TYPE_LABELS[value]}</Tag>
      ),
      filters: Object.entries(TAX_TYPE_LABELS).map(([value, label]) => ({
        text: label,
        value})),
      onFilter: (value: any, record: TaxRateListItem) => record.tax_type === value},
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name'},
    {
      title: 'Ставка',
      dataIndex: 'rate',
      key: 'rate',
      render: (value: number, record: TaxRateListItem) => (
        <div>
          <div>{rateToPercent(value)}</div>
          {record.rate_above_threshold && (
            <div style={{ fontSize: 12, color: '#999' }}>
              Выше порога: {rateToPercent(record.rate_above_threshold)}
            </div>
          )}
        </div>
      )},
    {
      title: 'Порог',
      dataIndex: 'threshold_amount',
      key: 'threshold_amount',
      render: (value: number | null) => (value ? value.toLocaleString('ru-RU') + ' ₽' : '—')},
    {
      title: 'Период действия',
      key: 'period',
      render: (_: any, record: TaxRateListItem) => (
        <div>
          <div>с {dayjs(record.effective_from).format('DD.MM.YYYY')}</div>
          <div>
            по {record.effective_to ? dayjs(record.effective_to).format('DD.MM.YYYY') : '∞'}
          </div>
        </div>
      )},
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => (
        <Tag color={value ? 'green' : 'red'}>{value ? 'Активна' : 'Отключена'}</Tag>
      )},
    {
      title: 'Действия',
      key: 'actions',
      width: 160,
      render: (_: any, record: TaxRateListItem) => (
        <Space>
          <Button type="link" onClick={() => handleModalOpen(record)}>
            Изменить
          </Button>
          <Popconfirm
            title="Удалить ставку?"
            okText="Удалить"
            cancelText="Отмена"
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" danger>
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      )},
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space size="large">
            <span style={{ fontSize: 20, fontWeight: 600 }}>
              <SafetyOutlined /> Справочник налоговых ставок
            </span>
            <Tag icon={<SettingOutlined />}>Глобальные ставки</Tag>
          </Space>
        </Col>
        <Col>
          <Space>
            <Tooltip title="Инициализировать ставки по умолчанию">
              <Button
                icon={<ReloadOutlined />}
                onClick={() => initMutation.mutate()}
                loading={initMutation.isPending}
              >
                Заполнить по умолчанию
              </Button>
            </Tooltip>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleModalOpen()}
            >
              Добавить ставку
            </Button>
          </Space>
        </Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Select
              allowClear
              placeholder="Тип налога"
              style={{ width: '100%' }}
              value={filters.taxType}
              onChange={(value) => setFilters((prev) => ({ ...prev, taxType: value }))}
              options={Object.entries(TAX_TYPE_LABELS).map(([value, label]) => ({
                value,
                label}))}
            />
          </Col>
          <Col span={6}>
            <Select
              allowClear
              placeholder="Статус"
              style={{ width: '100%' }}
              value={
                typeof filters.isActive === 'boolean'
                  ? filters.isActive
                    ? 'active'
                    : 'inactive'
                  : undefined
              }
              onChange={(value) =>
                setFilters((prev) => ({
                  ...prev,
                  isActive: value === undefined ? undefined : value === 'active'}))
              }
              options={[
                { value: 'active', label: 'Активные' },
                { value: 'inactive', label: 'Неактивные' },
              ]}
            />
          </Col>
          <Col span={6}>
            <DatePicker
              allowClear
              placeholder="Дата актуальности"
              style={{ width: '100%' }}
              value={filters.effectiveDate ? dayjs(filters.effectiveDate) : undefined}
              onChange={(value) =>
                setFilters((prev) => ({
                  ...prev,
                  effectiveDate: value ? value.format('YYYY-MM-DD') : undefined}))
              }
            />
          </Col>
          <Col span={6}>
            <Button
              onClick={() => setFilters({})}
              style={{ width: '100%' }}
              disabled={!filters.taxType && filters.isActive === undefined && !filters.effectiveDate}
            >
              Сбросить фильтры
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <ResponsiveTable
          loading={isLoading || isFetching}
          dataSource={taxRates}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          mobileLayout="card"
        />
      </Card>

      <Modal
        title={editingRate ? 'Изменение ставки' : 'Новая ставка'}
        open={isModalOpen}
        onCancel={handleModalClose}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnHidden
      >
        <Form layout="vertical" form={form}>
          <Form.Item
            label="Тип налога"
            name="tax_type"
            rules={[{ required: true, message: 'Выберите тип налога' }]}
          >
            <Select
              options={Object.entries(TAX_TYPE_LABELS).map(([value, label]) => ({
                value,
                label}))}
            />
          </Form.Item>

          <Form.Item
            label="Название"
            name="name"
            rules={[{ required: true, message: 'Введите название ставки' }]}
          >
            <Input placeholder="Например, НДФЛ 13%" />
          </Form.Item>

          <Form.Item label="Описание" name="description">
            <Input.TextArea rows={3} placeholder="Дополнительная информация" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Ставка"
                name="rate"
                rules={[{ required: true, message: 'Укажите ставку' }]}
              >
                <InputNumber
                  min={0}
                  max={1}
                  step={0.001}
                  placeholder="0.13"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Ставка выше порога" name="rate_above_threshold">
                <InputNumber min={0} max={1} step={0.001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Пороговая сумма" name="threshold_amount">
            <InputNumber
              min={0}
              step={1000}
              placeholder="Например, 5000000"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Дата начала действия"
                name="effective_from"
                rules={[{ required: true, message: 'Выберите дату начала' }]}
              >
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Дата окончания действия" name="effective_to">
                <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Активна" name="is_active" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>

          <Form.Item label="Примечания" name="notes">
            <Input.TextArea rows={2} placeholder="Основание, комментарий..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

