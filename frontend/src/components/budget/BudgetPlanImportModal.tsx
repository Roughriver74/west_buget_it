import { useState } from 'react';
import { Modal, Upload, message, Alert, Statistic, Row, Col, Typography, Button, Spin } from 'antd';
import { InboxOutlined, DownloadOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface BudgetPlanImportModalProps {
  visible: boolean;
  versionId: number | null;
  onCancel: () => void;
}

interface ImportResult {
  success: boolean;
  message: string;
  total_rows: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
}

export default function BudgetPlanImportModal({ visible, versionId, onCancel }: BudgetPlanImportModalProps) {
  const queryClient = useQueryClient();
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!versionId) throw new Error('Version ID is required');

      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(`/budget/versions/${versionId}/import`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setImportResult(data);
      if (data.success) {
        message.success('Импорт завершён успешно!');
        queryClient.invalidateQueries({ queryKey: ['budget-version', versionId] });
        queryClient.invalidateQueries({ queryKey: ['budget-plan-details', versionId] });
      } else {
        message.error('Импорт завершён с ошибками');
      }
    },
    onError: (error: any) => {
      message.error(`Ошибка импорта: ${error.response?.data?.detail || error.message || 'Неизвестная ошибка'}`);
    },
  });

  const handleUpload = async (file: File) => {
    setImportResult(null);
    await importMutation.mutateAsync(file);
    return false; // Prevent auto upload
  };

  const handleCancel = () => {
    if (!importMutation.isPending) {
      setFileList([]);
      setImportResult(null);
      onCancel();
    }
  };

  const handleClose = () => {
    setFileList([]);
    setImportResult(null);
    onCancel();
  };

  const handleDownloadTemplate = () => {
    // TODO: Implement template download endpoint
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const url = `${API_URL}/api/v1/templates/download/budget_plan`;

    const link = document.createElement('a');
    link.href = url;
    link.download = 'Шаблон_План_Бюджета.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    message.info('Скачивание шаблона начато');
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.xlsx,.xls',
    fileList,
    beforeUpload: (file: File) => {
      setFileList([file]);
      handleUpload(file);
      return false;
    },
    onRemove: () => {
      setFileList([]);
      setImportResult(null);
    },
  };

  return (
    <Modal
      title="Импорт плана бюджета из Excel"
      open={visible}
      onOk={importResult ? handleClose : undefined}
      onCancel={handleCancel}
      okText={importResult ? 'Закрыть' : undefined}
      cancelText={importResult ? undefined : 'Отмена'}
      width={800}
      confirmLoading={importMutation.isPending}
      cancelButtonProps={{ disabled: importMutation.isPending }}
      footer={importResult ? undefined : null}
    >
      {!importResult ? (
        <>
          <Alert
            message="Формат файла"
            description={
              <div>
                <p>Excel файл должен содержать следующие колонки:</p>
                <ul>
                  <li><Text strong>Категория</Text> - название категории бюджета (должна существовать в справочнике)</li>
                  <li><Text strong>Тип</Text> - OPEX или CAPEX</li>
                  <li><Text strong>Январь, Февраль, ..., Декабрь</Text> - суммы по месяцам (12 колонок)</li>
                  <li><Text strong>Обоснование</Text> - обоснование расходов (опционально)</li>
                </ul>
                <p style={{ marginTop: 10 }}>
                  <Text type="warning" strong>Важно:</Text> Категории должны быть предварительно созданы в справочнике категорий.
                  Если категория не найдена, строка будет пропущена.
                </p>
                <p style={{ marginTop: 10 }}>
                  <Text type="secondary">
                    Если план для категории на указанный месяц уже существует, он будет обновлён.
                  </Text>
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 20 }}
          />

          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownloadTemplate}
            style={{ marginBottom: 20 }}
            type="default"
          >
            Скачать шаблон Excel
          </Button>

          <Dragger {...uploadProps} disabled={importMutation.isPending}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              Нажмите или перетащите файл Excel в эту область
            </p>
            <p className="ant-upload-hint">
              Поддерживаются файлы .xlsx и .xls (макс. 10MB)
            </p>
          </Dragger>

          {importMutation.isPending && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text>Импорт данных... Пожалуйста, подождите.</Text>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          <Alert
            message={importResult.success ? 'Импорт завершён успешно' : 'Импорт завершён с ошибками'}
            description={importResult.message}
            type={importResult.success ? 'success' : 'warning'}
            showIcon
            style={{ marginBottom: 20 }}
          />

          <Row gutter={16} style={{ marginBottom: 20 }}>
            <Col span={6}>
              <Statistic
                title="Всего строк"
                value={importResult.total_rows}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Создано"
                value={importResult.created}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Обновлено"
                value={importResult.updated}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Пропущено"
                value={importResult.skipped}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>

          {importResult.errors && importResult.errors.length > 0 && (
            <>
              <Title level={5}>Ошибки импорта:</Title>
              <Alert
                message={
                  <div style={{ maxHeight: 200, overflow: 'auto' }}>
                    {importResult.errors.map((error, index) => (
                      <div key={index}>• {error}</div>
                    ))}
                    {importResult.skipped > importResult.errors.length && (
                      <div style={{ marginTop: 10, fontStyle: 'italic' }}>
                        И еще {importResult.skipped - importResult.errors.length} ошибок...
                      </div>
                    )}
                  </div>
                }
                type="error"
                showIcon
              />
            </>
          )}

          <Alert
            message="Что дальше?"
            description="Данные импортированы. Вы можете перейти к просмотру и редактированию плана или закрыть это окно."
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </>
      )}
    </Modal>
  );
}
