import { useState } from 'react';
import { Modal, Upload, App, Alert, Statistic, Row, Col, Typography, Button, Spin } from 'antd';
import { InboxOutlined, DownloadOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useDepartment } from '@/contexts/DepartmentContext';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface EmployeeImportModalProps {
  visible: boolean;
  onCancel: () => void;
}

interface ImportResult {
  success: boolean;
  message?: string;
  stats?: {
    total_rows: number;
    created: number;
    updated: number;
    skipped: number;
  };
  errors?: string[];
}

export default function EmployeeImportModal({ visible, onCancel }: EmployeeImportModalProps) {
  const queryClient = useQueryClient();
  const { message, modal } = App.useApp();
  const { selectedDepartment } = useDepartment();
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('entity_type', 'employees');

      // IMPORTANT: Pass department_id so employees are imported to the selected department
      if (selectedDepartment?.id) {
        formData.append('department_id', selectedDepartment.id.toString());
      }

      // Note: column_mapping is optional - the unified service will auto-detect columns
      // based on aliases defined in backend/app/import_configs/employees.json

      const response = await apiClient.post('/import/execute', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setImportResult(data);
      if (data.success) {
        message.success('Импорт сотрудников завершён успешно!');
        queryClient.invalidateQueries({ queryKey: ['employees'] });
      } else {
        message.error('Импорт завершён с ошибками');
      }
    },
    onError: (error: any) => {
      console.error('Import error details:', error.response?.data);
      console.error('Full error object:', error);
      const errorDetail = error.response?.data?.detail;
      const validationResult = error.response?.data?.validation_result;

      // Log more details for debugging
      if (typeof errorDetail === 'object') {
        console.error('Error detail object:', JSON.stringify(errorDetail, null, 2));
      }

      // Show detailed validation errors if available
      if (validationResult) {
        console.log('Validation result:', validationResult);
        const errorMessages = validationResult.messages?.filter((m: any) => m.severity === 'error') || [];
        if (errorMessages.length > 0) {
          modal.error({
            title: 'Ошибки валидации',
            content: (
              <div style={{ maxHeight: 400, overflow: 'auto' }}>
                {errorMessages.slice(0, 10).map((msg: any, index: number) => (
                  <div key={index} style={{ marginBottom: 8 }}>
                    <strong>Строка {msg.row}:</strong> {msg.message}
                    {msg.column && ` (колонка: ${msg.column})`}
                    {msg.value !== null && msg.value !== undefined && ` [значение: ${msg.value}]`}
                  </div>
                ))}
                {errorMessages.length > 10 && (
                  <div style={{ marginTop: 8, fontStyle: 'italic' }}>
                    ... и ещё {errorMessages.length - 10} ошибок
                  </div>
                )}
              </div>
            ),
            width: 600,
          });
          return;
        }
      }

      message.error(`Ошибка импорта: ${errorDetail || error.message || 'Неизвестная ошибка'}`);
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

  const handleDownloadTemplate = async () => {
    try {
      // Use apiClient to avoid double /api/v1 prefix
      const response = await apiClient.get('/import/template/employees', {
        params: {
          language: 'ru',
          include_examples: true
        },
        responseType: 'blob'
      });

      // Create blob and download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = 'Шаблон_Импорт_Сотрудников.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      message.success('Шаблон успешно скачан');
    } catch (error) {
      message.error('Ошибка при скачивании шаблона');
    }
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
      title="Импорт сотрудников из Excel"
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
                  <li><Text strong>ФИО</Text> - полное имя сотрудника (обязательно)</li>
                  <li><Text strong>Должность</Text> - должность сотрудника (обязательно)</li>
                  <li><Text strong>Базовый оклад</Text> или <Text strong>Оклад</Text> - размер оклада (обязательно)</li>
                  <li><Text strong>Табельный номер</Text> - табельный номер (опционально)</li>
                  <li><Text strong>Дата рождения</Text> - дата рождения для различения полных тёзок (опционально)</li>
                  <li><Text strong>Месячная премия</Text> - ежемесячная премия (опционально)</li>
                  <li><Text strong>Квартальная премия</Text> - премия раз в квартал (опционально)</li>
                  <li><Text strong>Годовая премия</Text> - премия раз в год (опционально)</li>
                  <li><Text strong>Дата приема</Text> - дата приема на работу (опционально)</li>
                </ul>
                <p style={{ marginTop: 10 }}>
                  <Text type="warning" strong>Важно:</Text> Система автоматически определит колонки по названиям.
                  Поддерживаются различные варианты названий.
                </p>
                <p style={{ marginTop: 10 }}>
                  <Text type="secondary">
                    Если сотрудник с таким ФИО уже существует, его данные будут обновлены.
                    Все сотрудники импортируются со статусом "Активен" по умолчанию.
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

          {importResult.stats && (
            <Row gutter={16} style={{ marginBottom: 20 }}>
              <Col span={6}>
                <Statistic
                  title="Всего строк"
                  value={importResult.stats.total_rows}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Создано"
                  value={importResult.stats.created}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Обновлено"
                  value={importResult.stats.updated}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Пропущено"
                  value={importResult.stats.skipped}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
            </Row>
          )}

          {importResult.errors && importResult.errors.length > 0 && (
            <>
              <Title level={5}>Ошибки импорта:</Title>
              <Alert
                message={
                  <div style={{ maxHeight: 200, overflow: 'auto' }}>
                    {importResult.errors.map((error: any, index: number) => {
                      // Handle both string errors and object errors {row, error}
                      const errorText = typeof error === 'string'
                        ? error
                        : error.error || error.message || JSON.stringify(error);
                      const rowPrefix = typeof error === 'object' && error.row
                        ? `Строка ${error.row}: `
                        : '';

                      return (
                        <div key={index}>• {rowPrefix}{errorText}</div>
                      );
                    })}
                  </div>
                }
                type="error"
                showIcon
              />
            </>
          )}

          <Alert
            message="Что дальше?"
            description="Данные импортированы. Вы можете перейти к просмотру списка сотрудников или закрыть это окно."
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </>
      )}
    </Modal>
  );
}
