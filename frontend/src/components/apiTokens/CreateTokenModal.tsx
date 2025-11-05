import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, DatePicker, Checkbox, Space, Alert } from 'antd';
import { useQuery } from '@tanstack/react-query';
import type { CreateTokenRequest, APITokenScope } from '../../types/apiToken';
import { getDepartments } from '../../api/departments';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

interface CreateTokenModalProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values: CreateTokenRequest) => Promise<void>;
  loading?: boolean;
}

const SCOPE_OPTIONS: { value: APITokenScope; label: string; description: string }[] = [
  { value: 'READ', label: 'READ', description: 'Чтение и экспорт данных' },
  { value: 'WRITE', label: 'WRITE', description: 'Создание и обновление записей' },
  { value: 'DELETE', label: 'DELETE', description: 'Удаление записей' },
  { value: 'ADMIN', label: 'ADMIN', description: 'Полный доступ (включает все scope)' }
];

const CreateTokenModal: React.FC<CreateTokenModalProps> = ({
  visible,
  onCancel,
  onSubmit,
  loading = false
}) => {
  const [form] = Form.useForm();
  const [selectedScopes, setSelectedScopes] = useState<APITokenScope[]>([]);

  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: getDepartments
  });

  useEffect(() => {
    if (!visible) {
      form.resetFields();
      setSelectedScopes([]);
    }
  }, [visible, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();

      const request: CreateTokenRequest = {
        name: values.name,
        description: values.description,
        scopes: values.scopes,
        department_id: values.department_id,
        expires_at: values.expires_at ? values.expires_at.toISOString() : undefined
      };

      await onSubmit(request);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleScopesChange = (scopes: APITokenScope[]) => {
    // If ADMIN is selected, auto-select all scopes
    if (scopes.includes('ADMIN')) {
      setSelectedScopes(['READ', 'WRITE', 'DELETE', 'ADMIN']);
      form.setFieldsValue({ scopes: ['READ', 'WRITE', 'DELETE', 'ADMIN'] });
    } else {
      setSelectedScopes(scopes);
    }
  };

  return (
    <Modal
      title="Создать новый API токен"
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      okText="Создать"
      cancelText="Отмена"
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          scopes: ['READ']
        }}
      >
        <Alert
          message="Токен будет показан только один раз!"
          description="После создания токена вы увидите его в следующем окне. Обязательно скопируйте его сразу - повторно получить токен будет невозможно."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form.Item
          name="name"
          label="Название токена"
          rules={[
            { required: true, message: 'Введите название токена' },
            { min: 3, message: 'Минимум 3 символа' },
            { max: 100, message: 'Максимум 100 символов' }
          ]}
        >
          <Input placeholder="Например: Production ERP Integration" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Описание"
        >
          <TextArea
            placeholder="Для чего используется этот токен..."
            rows={3}
          />
        </Form.Item>

        <Form.Item
          name="scopes"
          label="Права доступа (Scopes)"
          rules={[{ required: true, message: 'Выберите хотя бы один scope' }]}
        >
          <Checkbox.Group
            style={{ width: '100%' }}
            onChange={(values) => handleScopesChange(values as APITokenScope[])}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {SCOPE_OPTIONS.map((scope) => (
                <Checkbox key={scope.value} value={scope.value}>
                  <strong>{scope.label}</strong>: {scope.description}
                </Checkbox>
              ))}
            </Space>
          </Checkbox.Group>
        </Form.Item>

        <Form.Item
          name="department_id"
          label="Департамент (опционально)"
          tooltip="Если указан, токен будет видеть только данные этого департамента. Оставьте пустым для системного токена."
        >
          <Select
            placeholder="Выберите департамент"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {departments?.map((dept) => (
              <Option key={dept.id} value={dept.id}>
                {dept.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="expires_at"
          label="Срок действия (опционально)"
          tooltip="Дата, когда токен автоматически станет недействительным. Оставьте пустым для бессрочного токена."
        >
          <DatePicker
            style={{ width: '100%' }}
            format="DD.MM.YYYY"
            placeholder="Выберите дату"
            disabledDate={(current) => current && current < dayjs().startOf('day')}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateTokenModal;
