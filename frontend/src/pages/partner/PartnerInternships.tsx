import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Badge, Tabs } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import type { InternshipRequest } from '../../api/partner';
import InternshipCard from '../../components/InternshipCard';

const { Title, Text } = Typography;

const PartnerInternships: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<InternshipRequest[]>([]);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchInternships();
  }, []);

  const fetchInternships = async () => {
    setLoading(true);
    try {
      const response = await partnerAPI.getInternships();
      setRequests(response.data || []);
    } catch (error) {
      console.error(error);
      message.error('Не удалось загрузить приглашения на стажировку');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (internshipId: number, newStatus: string) => {
    await partnerAPI.updateInternshipStatus(internshipId, newStatus);
    await fetchInternships();
  };

  const getFilteredRequests = (status?: string) => {
    if (!status) return requests;
    return requests.filter(r => r.status === status);
  };

  const statusCounts = {
    sent: requests.filter(r => r.status === 'sent').length,
    accepted: requests.filter(r => r.status === 'accepted').length,
    in_progress: requests.filter(r => r.status === 'in_progress').length,
    rejected: requests.filter(r => r.status === 'rejected').length,
    completed: requests.filter(r => r.status === 'completed').length,
  };

  const tabItems = [
    {
      key: 'all',
      label: (
        <Badge
          count={requests.length}
          style={{
            backgroundColor: '#00AEEF',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          Все приглашения
        </Badge>
      ),
    },
    {
      key: 'sent',
      label: (
        <Badge
          count={statusCounts.sent}
          style={{
            backgroundColor: '#1890ff',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          Отправлено
        </Badge>
      ),
    },
    {
      key: 'accepted',
      label: (
        <Badge
          count={statusCounts.accepted}
          style={{
            backgroundColor: '#52c41a',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          Принято
        </Badge>
      ),
    },
    {
      key: 'in_progress',
      label: (
        <Badge
          count={statusCounts.in_progress}
          style={{
            backgroundColor: '#faad14',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          В процессе
        </Badge>
      ),
    },
    {
      key: 'rejected',
      label: (
        <Badge
          count={statusCounts.rejected}
          style={{
            backgroundColor: '#ff4d4f',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          Отклонено
        </Badge>
      ),
    },
    {
      key: 'completed',
      label: (
        <Badge
          count={statusCounts.completed}
          style={{
            backgroundColor: '#722ed1',
            color: '#fff',
            padding: '0 6px',
            borderRadius: '2px',
            marginLeft: '8px',
          }}
        >
          Завершено
        </Badge>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  const filteredRequests = getFilteredRequests(activeTab === 'all' ? undefined : activeTab);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>
          💼 Приглашения на стажировку
        </Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      <Card style={{ marginBottom: 24, background: '#f0f7ff', borderColor: '#00AEEF' }}>
        <div style={{ display: 'flex', justifyContent: 'space-around' }}>
          <div style={{ textAlign: 'center' }}>
            <Text strong style={{ fontSize: 18, color: '#00AEEF' }}>{requests.length}</Text>
            <br />
            <Text type="secondary">Всего отправлено</Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text strong style={{ fontSize: 18, color: '#52c41a' }}>{statusCounts.accepted}</Text>
            <br />
            <Text type="secondary">Принято студентами</Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text strong style={{ fontSize: 18, color: '#faad14' }}>{statusCounts.in_progress}</Text>
            <br />
            <Text type="secondary">В процессе</Text>
          </div>
        </div>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />

      {filteredRequests.length === 0 ? (
        <Card>
          <Empty
            description={
              activeTab === 'all'
                ? 'Приглашения на стажировку не отправлены'
                : 'По этому статусу нет приглашений'
            }
          />
        </Card>
      ) : (
        filteredRequests.map(request => (
          <InternshipCard
            key={request.id}
            request={request}
            onStatusChange={handleStatusChange}
          />
        ))
      )}
    </div>
  );
};

export default PartnerInternships;