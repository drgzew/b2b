// frontend/src/pages/author/AuthorInternships.tsx
import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Space, Tag } from 'antd';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { authorAPI } from '../../api/author';
import type { Internship } from '../../api/types';
import type { AuthorLayoutContextType } from '../../layouts/AuthorLayout';

const { Title, Text } = Typography;

const AuthorInternships: React.FC = () => {
  const navigate = useNavigate();
  const { refreshCounts } = useOutletContext<AuthorLayoutContextType>();
  const [loading, setLoading] = useState(true);
  const [internships, setInternships] = useState<Internship[]>([]);

  useEffect(() => {
    fetchInternships();
  }, []);

  const fetchInternships = async () => {
    setLoading(true);
    try {
      const response = await authorAPI.getInternships();
      setInternships(response.data || []);
    } catch (error: any) {
      console.error('Ошибка загрузки стажировок:', error);
      message.error(error.response?.data?.detail || 'Не удалось загрузить приглашения на стажировку');
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (internshipId: number, accept: boolean) => {
    try {
      await authorAPI.respondToInternship(internshipId, accept);
      message.success(accept ? 'Приглашение принято' : 'Приглашение отклонено');
      await fetchInternships();
      refreshCounts();
    } catch (error: any) {
      console.error('Ошибка ответа на приглашение:', error);
      message.error(error.response?.data?.detail || 'Ошибка при ответе на приглашение');
    }
  };

  const statusColorMap: Record<string, string> = {
    sent: 'blue',
    accepted: 'green',
    in_progress: 'orange',
    rejected: 'red',
    completed: 'gray',
    cancelled: 'default',
  };

  const statusLabelMap: Record<string, string> = {
    sent: 'Отправлено',
    accepted: 'Принято',
    in_progress: 'В процессе',
    rejected: 'Отклонено',
    completed: 'Завершено',
    cancelled: 'Отменено',
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
        <Title level={4}>💼 Приглашения на стажировку</Title>
        <Button onClick={() => navigate('/author/dashboard')}>← На дашборд</Button>
      </div>

      {internships.length === 0 ? (
        <Card>
          <Empty description="Пока нет приглашений на стажировку" />
        </Card>
      ) : (
        internships.map((inv) => (
          <Card key={inv.id} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Title level={5}>{inv.artifact_title || `Артефакт #${inv.artifact_id}`}</Title>
                <Text type="secondary">Компания: {inv.partner_name || 'Не указана'}</Text>
                <br />
                <Text type="secondary">Создано: {new Date(inv.created_at).toLocaleDateString()}</Text>
                {inv.response_date && (
                  <>
                    <br />
                    <Text type="secondary">Ответ: {new Date(inv.response_date).toLocaleDateString()}</Text>
                  </>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                {inv.status === 'sent' ? (
                  <Space style={{ marginTop: 8 }}>
                    <Button
                      type="primary"
                      size="small"
                      style={{ background: '#52c41a' }}
                      onClick={() => handleRespond(inv.id, true)}
                    >
                      Принять
                    </Button>
                    <Button
                      danger
                      size="small"
                      onClick={() => handleRespond(inv.id, false)}
                    >
                      Отклонить
                    </Button>
                  </Space>
                ) : (
                  <Tag color={statusColorMap[inv.status] || 'default'}>
                    {statusLabelMap[inv.status] || inv.status}
                  </Tag>
                )}
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  );
};

export default AuthorInternships;