import { useState } from 'react';
import { Modal, Upload, message, Alert, Statistic, Row, Col, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';

const { Dragger } = Upload;
const { Title } = Typography;

interface PayrollImportModalProps {
  visible: boolean;
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

export default function PayrollImportModal({ visible, onCancel }: PayrollImportModalProps) {
  const queryClient = useQueryClient();
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/payroll/plans/import', formData, {
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
        queryClient.invalidateQueries({ queryKey: ['payroll-plans'] });
        queryClient.invalidateQueries({ queryKey: ['payroll-dynamics'] });
        queryClient.invalidateQueries({ queryKey: ['payroll-structure'] });
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
      title="Импорт планов ФОТ из Excel"
      open={visible}
      onOk={importResult ? handleClose : undefined}
      onCancel={handleCancel}
      okText={importResult ? 'Закрыть' : undefined}
      cancelText={importResult ? undefined : 'Отмена'}
      width={700}
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
                <p>Файл должен содержать следующие колонки:</p>
                <ul>
                  <li><strong>Год</strong> - год планирования (например, 2025)</li>
                  <li><strong>Месяц</strong> - номер месяца (1-12)</li>
                  <li><strong>Сотрудник</strong> - полное имя сотрудника (должен существовать в базе)</li>
                  <li><strong>Оклад</strong> - базовый оклад</li>
                  <li><strong>Премия</strong> - сумма премии (опционально)</li>
                  <li><strong>Прочие выплаты</strong> - прочие выплаты (опционально)</li>
                  <li><strong>Примечания</strong> - дополнительные примечания (опционально)</li>
                </ul>
                <p style={{ marginTop: 10 }}>
                  <strong>Примечание:</strong> Если план для сотрудника на указанный месяц уже существует,
                  он будет обновлён. Все сотрудники должны быть предварительно добавлены в систему.
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 20 }}
          />

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
        </>
      )}
    </Modal>
  );
}
