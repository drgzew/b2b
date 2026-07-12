import React from 'react';
import { Card, Typography, Tag, Button, Space, Popconfirm, message } from 'antd';
import type { InternshipRequest } from '../api/partner';

const { Title, Text } = Typography;

interface InternshipCardProps {
  request: InternshipRequest;
  onStatusChange: (requestId: number, newStatus: string) => Promise<void>;
}

const getStatusLabel = (status: string) => {
  const statusMap: Record<string, { label: string; color: string }> = {
    sent: { label: 'Отправлено', color: 'blue' },
    accepted: { label: 'Принято студентом', color: 'green' },
    in_progress: { label: 'В процессе', color: 'orange' },
    rejected: { label: 'Отклонено студентом', color: 'red' },
    completed: { label: 'Завершено', color: 'purple' },
  };
  return statusMap[status] || { label: status, color: 'default' };
};

const getDaysAgo = (dateString: string): number => {
  const createdDate = new Date(dateString);
  const today = new Date();
  const timeDiff = today.getTime() - createdDate.getTime();
  const daysDiff = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
  return daysDiff;
};

const formatDaysAgo = (days: number): string => {
  if (days === 0) return 'сегодня';
  if (days === 1) return '1 день назад';
  if (days < 5) return `${days} дня назад`;
  return `${days} дней назад`;
};

const InternshipCard: React.FC<InternshipCardProps> = ({ request, onStatusChange }) => {
  const statusInfo = getStatusLabel(request.status);
  const daysAgo = getDaysAgo(request.created_at);
  const [loading, setLoading] = React.useState(false);

  const handleStatusChange = async (newStatus: string) => {
    setLoading(true);
    try {
      await onStatusChange(request.id, newStatus);
      message.success(`Статус обновлён на "${getStatusLabel(newStatus).label}"`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось обновить статус');
    } finally {
      setLoading(false);
    }
  };

  const availableStatuses = [
    { value: 'accepted', label: 'Принято' },
    { value: 'in_progress', label: 'В процессе' },
    { value: 'rejected', label: 'Отклонено' },
    { value: 'completed', label: 'Завершено' },
  ];

  return (
    <Card style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div style={{ flex: 1 }}>
          <Title level={5}>{request.artifact.title}</Title>
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary">{request.artifact.author_name || 'Автор не указан'}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              📅 Приглашение отправлено {formatDaysAgo(daysAgo)}
            </Text>
          </div>
          {request.student_name && (
            <div style={{ marginBottom: 8 }}>
              <Text strong>Студент: </Text>
              <Text>{request.student_name}</Text>
            </div>
          )}
          <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
        </div>
        <Space>
          {request.status !== 'completed' && request.status !== 'rejected' && (
            <Popconfirm
              title="Изменить статус"
              description="Выберите новый статус приглашения"
              okText="Применить"
              cancelText="Отмена"
            >
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {availableStatuses.map(status => (
                  <Button
                    key={status.value}
                    size="small"
                    type={request.status === status.value ? 'primary' : 'default'}
                    onClick={() => handleStatusChange(status.value)}
                    loading={loading}
                  >
                    {status.label}
                  </Button>
                ))}
              </div>
            </Popconfirm>
          )}
        </Space>
      </div>
    </Card>
  );
};

export default InternshipCard;