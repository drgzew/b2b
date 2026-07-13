import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Tabs } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import InternshipCard from '../../components/InternshipCard';
import type { Internship } from '../../api/types';

const { Title, Text } = Typography;

const PartnerInternships: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [internships, setInternships] = useState<Internship[]>([]);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchInternships();
  }, []);

  const fetchInternships = async () => {
    setLoading(true);
    try {
      const res = await partnerAPI.getInternships();
      setInternships(res.data || []);
    } catch (error) {
      message.error('Не удалось загрузить стажировки');
    } finally {
      setLoading(false);
    }
  };

  const getFiltered = (status?: string) => {
    if (!status) return internships;
    return internships.filter(i => i.status === status);
  };

  const statusCounts = {
    sent: internships.filter(i => i.status === 'sent').length,
    accepted: internships.filter(i => i.status === 'accepted').length,
    in_progress: internships.filter(i => i.status === 'in_progress').length,
    rejected: internships.filter(i => i.status === 'rejected').length,
    completed: internships.filter(i => i.status === 'completed').length,
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;

  const filtered = getFiltered(activeTab === 'all' ? undefined : activeTab);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>💼 Приглашения на стажировку</Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 24 }}>
          <div><Text type="secondary">Всего</Text><br /><Text strong style={{ fontSize: 24 }}>{internships.length}</Text></div>
          <div><Text type="secondary">Принято</Text><br /><Text strong style={{ fontSize: 24, color: '#52c41a' }}>{statusCounts.accepted}</Text></div>
          <div><Text type="secondary">В процессе</Text><br /><Text strong style={{ fontSize: 24, color: '#faad14' }}>{statusCounts.in_progress}</Text></div>
        </div>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'all', label: `Все (${internships.length})` },
          { key: 'sent', label: `Отправлено (${statusCounts.sent})` },
          { key: 'accepted', label: `Принято (${statusCounts.accepted})` },
          { key: 'in_progress', label: `В процессе (${statusCounts.in_progress})` },
          { key: 'rejected', label: `Отклонено (${statusCounts.rejected})` },
          { key: 'completed', label: `Завершено (${statusCounts.completed})` },
        ]}
      />

      {filtered.length === 0 ? (
        <Card><Empty description="Нет приглашений в этом статусе" /></Card>
      ) : (
        filtered.map(inv => <InternshipCard key={inv.id} internship={inv} showControls={false} />)
      )}
    </div>
  );
};

export default PartnerInternships;