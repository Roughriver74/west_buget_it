import React, { useState } from 'react';
import { Modal, Alert, Input, Button, Space, Typography } from 'antd';
import { CopyOutlined, CheckOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface ShowTokenModalProps {
  visible: boolean;
  tokenKey: string | null;
  tokenName: string;
  onClose: () => void;
}

/**
 * Modal для показа нового API токена
 *
 * ВАЖНО: Токен показывается ТОЛЬКО ОДИН РАЗ при создании!
 * После закрытия модального окна токен не может быть восстановлен.
 */
const ShowTokenModal: React.FC<ShowTokenModalProps> = ({
  visible,
  tokenKey,
  tokenName,
  onClose
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!tokenKey) return;

    try {
      await navigator.clipboard.writeText(tokenKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy token:', error);
    }
  };

  return (
    <Modal
      title={
        <Space>
          <ExclamationCircleOutlined style={{ color: '#faad14' }} />
          <span>Токен создан успешно</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" type="primary" onClick={onClose} danger>
          Я скопировал токен, закрыть
        </Button>
      ]}
      width={700}
      maskClosable={false}
      closable={false}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Alert
          message="⚠️ СОХРАНИТЕ ЭТОТ ТОКЕН СЕЙЧАС!"
          description="Токен показывается только один раз и не может быть восстановлен. Скопируйте его в безопасное место прямо сейчас!"
          type="warning"
          showIcon
        />

        <div>
          <Text strong>Название токена:</Text>
          <Paragraph code>{tokenName}</Paragraph>
        </div>

        <div>
          <Text strong>API Token:</Text>
          <Input.TextArea
            value={tokenKey || ''}
            readOnly
            autoSize={{ minRows: 3, maxRows: 5 }}
            style={{
              fontFamily: 'monospace',
              fontSize: '12px',
              marginTop: '8px'
            }}
          />
          <Button
            type="default"
            icon={copied ? <CheckOutlined /> : <CopyOutlined />}
            onClick={handleCopy}
            style={{ marginTop: '8px' }}
            block
          >
            {copied ? 'Скопировано!' : 'Скопировать токен'}
          </Button>
        </div>

        <Alert
          message="Как использовать токен"
          description={
            <div>
              <p>Добавьте токен в заголовок Authorization ваших HTTP запросов:</p>
              <code style={{ display: 'block', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                Authorization: Bearer {tokenKey?.substring(0, 20)}...
              </code>
              <p style={{ marginTop: '8px' }}>
                Пример с curl:
              </p>
              <code style={{ display: 'block', padding: '8px', background: '#f5f5f5', borderRadius: '4px', fontSize: '11px' }}>
                curl -H "Authorization: Bearer {tokenKey?.substring(0, 20)}..." http://api.example.com/endpoint
              </code>
            </div>
          }
          type="info"
        />
      </Space>
    </Modal>
  );
};

export default ShowTokenModal;
