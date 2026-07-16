import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Space, Tag } from 'antd';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { authorAPI } from '../../api/author';
import type { AuthorRequest } from '../../api/types';
import type { AuthorLayoutContextType } from '../../layouts/AuthorLayout';

const { Title, Text } = Typography;

const AuthorRequests: React.FC = () => {
  const navigate = useNavigate();
  const { refreshCounts } = useOutletContext<AuthorLayoutContextType>();
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<AuthorRequest[]>([]);

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await authorAPI.getRequests();
      setRequests(res.data || []);
    } catch (error) {
      message.error('Не удалось загрузить запросы');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (requestId: number, approve: boolean) => {
    try {
      await authorAPI.decideOnRequest(requestId, approve);
      message.success(approve ? 'Доступ предоставлен' : 'Запрос отклонён');
      await fetchRequests();
      // ✅ Обновляем счётчик в шапке
      refreshCounts();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>Запросы на полный текст</Title>
        <Button onClick={() => navigate('/author/dashboard')}>← На дашборд</Button>
      </div>

      {requests.length === 0 ? (
        <Card>
          <Empty description="Нет запросов на ваши работы" />
        </Card>
      ) : (
        requests.map((req) => (
          <Card key={req.id} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Title level={5}>{req.artifact_title}</Title>
                <Text>Компания: {req.partner_name}</Text>
                <br />
                <Text>Статус: <Tag color={req.status === 'sent' ? 'blue' : 'green'}>{req.status}</Tag></Text>
              </div>
              {req.status === 'sent' && (
                <Space>
                  <Button type="primary" onClick={() => handleDecision(req.id, true)}>
                    Разрешить
                  </Button>
                  <Button danger onClick={() => handleDecision(req.id, false)}>
                    Отклонить
                  </Button>
                </Space>
              )}
            </div>
          </Card>
        ))
      )}
    </div>
  );
};

export default AuthorRequests;