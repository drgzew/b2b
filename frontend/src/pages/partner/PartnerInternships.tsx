import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Tabs, Tag, Space, Popconfirm } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
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

  const handleStatusChange = async (internshipId: number, newStatus: string) => {
    try {
      await partnerAPI.updateInternshipStatus(internshipId, newStatus);
      message.success('Статус обновлён');
      await fetchInternships();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка обновления статуса');
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
    cancelled: internships.filter(i => i.status === 'cancelled').length,
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

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;

  const filtered = getFiltered(activeTab === 'all' ? undefined : activeTab);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>💼 Приглашения на стажировку</Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div><Text type="secondary">Всего</Text><br /><Text strong style={{ fontSize: 24 }}>{internships.length}</Text></div>
          <div><Text type="secondary">Отправлено</Text><br /><Text strong style={{ fontSize: 24, color: '#1890ff' }}>{statusCounts.sent}</Text></div>
          <div><Text type="secondary">Принято</Text><br /><Text strong style={{ fontSize: 24, color: '#52c41a' }}>{statusCounts.accepted}</Text></div>
          <div><Text type="secondary">В процессе</Text><br /><Text strong style={{ fontSize: 24, color: '#faad14' }}>{statusCounts.in_progress}</Text></div>
          <div><Text type="secondary">Отменено</Text><br /><Text strong style={{ fontSize: 24, color: '#d9d9d9' }}>{statusCounts.cancelled}</Text></div>
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
          { key: 'cancelled', label: `Отменено (${statusCounts.cancelled})` },
        ]}
      />

      {filtered.length === 0 ? (
        <Card><Empty description="Нет приглашений в этом статусе" /></Card>
      ) : (
        filtered.map(inv => (
          <Card key={inv.id} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Title level={5}>{inv.artifact_title || `Артефакт #${inv.artifact_id}`}</Title>
                <Text type="secondary">Студент: {inv.student_name || 'Не указан'}</Text>
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
                <Tag color={statusColorMap[inv.status] || 'default'}>
                  {statusLabelMap[inv.status] || inv.status}
                </Tag>
                {/* ✅ Для статуса 'sent' — только кнопка «Отменить» */}
                {inv.status === 'sent' && (
                  <div style={{ marginTop: 8 }}>
                    <Popconfirm
                      title="Отменить приглашение?"
                      description="Это действие нельзя отменить"
                      onConfirm={() => handleStatusChange(inv.id, 'cancelled')}
                      okText="Да"
                      cancelText="Нет"
                    >
                      <Button size="small" danger>Отменить</Button>
                    </Popconfirm>
                  </div>
                )}
                {inv.status === 'accepted' && (
                  <div style={{ marginTop: 8 }}>
                    <Button size="small" onClick={() => handleStatusChange(inv.id, 'in_progress')}>
                      Начать
                    </Button>
                    <Button size="small" danger onClick={() => handleStatusChange(inv.id, 'rejected')}>
                      Отклонить
                    </Button>
                  </div>
                )}
                {inv.status === 'in_progress' && (
                  <div style={{ marginTop: 8 }}>
                    <Button size="small" onClick={() => handleStatusChange(inv.id, 'completed')}>
                      Завершить
                    </Button>
                    <Button size="small" danger onClick={() => handleStatusChange(inv.id, 'rejected')}>
                      Отклонить
                    </Button>
                  </div>
                )}
                {(inv.status === 'rejected' || inv.status === 'completed' || inv.status === 'cancelled') && (
                  <div style={{ marginTop: 8 }}>
                    <Tag color={statusColorMap[inv.status]}>{statusLabelMap[inv.status]}</Tag>
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  );
};

export default PartnerInternships;