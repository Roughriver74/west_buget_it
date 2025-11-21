import React, { useState } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Tooltip,
  Typography
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  StopOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ru';

import AppLayout from '../components/common/AppLayout';
import { ResponsiveTable } from '@/components/common/ResponsiveTable';
import CreateTokenModal from '../components/apiTokens/CreateTokenModal';
import ShowTokenModal from '../components/apiTokens/ShowTokenModal';
import * as apiTokensApi from '../api/apiTokens';
import type { APIToken, APITokenWithKey, CreateTokenRequest, APITokenStatus, APITokenScope } from '../types/apiToken';

dayjs.extend(relativeTime);
dayjs.locale('ru');

const { Title, Text } = Typography;
const { confirm } = Modal;

const ApiTokensPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState<{
    visible: boolean;
    tokenKey: string | null;
    tokenName: string;
  }>({
    visible: false,
    tokenKey: null,
    tokenName: ''
  });

  // Fetch tokens
  const { data: tokens, isLoading } = useQuery({
    queryKey: ['api-tokens'],
    queryFn: () => apiTokensApi.getTokens()
  });

  // Create token mutation
  const createMutation = useMutation({
    mutationFn: (request: CreateTokenRequest) => apiTokensApi.createToken(request),
    onSuccess: (data: APITokenWithKey) => {
      message.success('Токен успешно создан');
      setCreateModalVisible(false);
      // Show token (only once!)
      setShowTokenModal({
        visible: true,
        tokenKey: data.token_key,
        tokenName: data.name
      });
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] });
    },
    onError: (error: any) => {
      message.error(`Ошибка создания токена: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Revoke token mutation
  const revokeMutation = useMutation({
    mutationFn: (tokenId: number) => apiTokensApi.revokeToken(tokenId),
    onSuccess: () => {
      message.success('Токен отозван');
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] });
    },
    onError: (error: any) => {
      message.error(`Ошибка отзыва токена: ${error.response?.data?.detail || error.message}`);
    }
  });

  // Delete token mutation
  const deleteMutation = useMutation({
    mutationFn: (tokenId: number) => apiTokensApi.deleteToken(tokenId),
    onSuccess: () => {
      message.success('Токен удален');
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] });
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления токена: ${error.response?.data?.detail || error.message}`);
    }
  });

  const handleRevokeToken = (token: APIToken) => {
    confirm({
      title: 'Отозвать токен?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>Вы уверены, что хотите отозвать токен <strong>{token.name}</strong>?</p>
          <p>Это действие необратимо. Все запросы с этим токеном будут отклонены.</p>
        </div>
      ),
      okText: 'Отозвать',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => revokeMutation.mutate(token.id)
    });
  };

  const handleDeleteToken = (token: APIToken) => {
    confirm({
      title: 'Удалить токен навсегда?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>⚠️ ОПАСНО!</strong></p>
          <p>Вы уверены, что хотите УДАЛИТЬ токен <strong>{token.name}</strong>?</p>
          <p>Это действие удалит токен из базы данных без возможности восстановления.</p>
        </div>
      ),
      okText: 'Удалить навсегда',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => deleteMutation.mutate(token.id)
    });
  };

  const getStatusTag = (status: APITokenStatus) => {
    const statusConfig = {
      ACTIVE: { color: 'success', text: 'Активен' },
      REVOKED: { color: 'error', text: 'Отозван' },
      EXPIRED: { color: 'default', text: 'Истек' }
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getScopeTag = (scope: APITokenScope) => {
    const scopeConfig = {
      READ: { color: 'blue' },
      WRITE: { color: 'green' },
      DELETE: { color: 'orange' },
      ADMIN: { color: 'red' }
    };
    return <Tag color={scopeConfig[scope]?.color}>{scope}</Tag>;
  };

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: APIToken) => (
        <div>
          <div><strong>{text}</strong></div>
          {record.description && (
            <div style={{ fontSize: '12px', color: '#888' }}>{record.description}</div>
          )}
        </div>
      )
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: APITokenStatus) => getStatusTag(status)
    },
    {
      title: 'Права доступа',
      dataIndex: 'scopes',
      key: 'scopes',
      width: 200,
      render: (scopes: APITokenScope[]) => (
        <Space size="small" wrap>
          {scopes.map(scope => getScopeTag(scope))}
        </Space>
      )
    },
    {
      title: 'Последнее использование',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 150,
      render: (date: string | null, record: APIToken) => (
        <div>
          {date ? (
            <>
              <Tooltip title={dayjs(date).format('DD.MM.YYYY HH:mm')}>
                <div>{dayjs(date).fromNow()}</div>
              </Tooltip>
              <div style={{ fontSize: '12px', color: '#888' }}>
                {record.request_count} запросов
              </div>
            </>
          ) : (
            <Text type="secondary">Не использовался</Text>
          )}
        </div>
      )
    },
    {
      title: 'Истекает',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 120,
      render: (date: string | null) => (
        date ? (
          <Tooltip title={dayjs(date).format('DD.MM.YYYY HH:mm')}>
            {dayjs(date).fromNow()}
          </Tooltip>
        ) : (
          <Text type="secondary">Бессрочный</Text>
        )
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_: any, record: APIToken) => (
        <Space size="small">
          {record.status === 'ACTIVE' && (
            <Tooltip title="Отозвать токен">
              <Button
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleRevokeToken(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="Удалить токен">
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteToken(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <AppLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>API Токены</Title>
            <Text type="secondary">
              Управление токенами для доступа к External API
            </Text>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            Создать токен
          </Button>
        </div>

        <Card>
          <ResponsiveTable
            columns={columns}
            dataSource={tokens}
            rowKey="id"
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Всего токенов: ${total}`
            }}
            mobileLayout="card"
          />
        </Card>

        <CreateTokenModal
          visible={createModalVisible}
          onCancel={() => setCreateModalVisible(false)}
          onSubmit={async (values) => {
            await createMutation.mutateAsync(values);
          }}
          loading={createMutation.isPending}
        />

        <ShowTokenModal
          visible={showTokenModal.visible}
          tokenKey={showTokenModal.tokenKey}
          tokenName={showTokenModal.tokenName}
          onClose={() => setShowTokenModal({ visible: false, tokenKey: null, tokenName: '' })}
        />
      </div>
    </AppLayout>
  );
};

export default ApiTokensPage;
