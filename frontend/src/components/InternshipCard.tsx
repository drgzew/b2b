import React from 'react';
import { Card, Typography, Tag, Button, Space, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { Internship } from '../api/types';

const { Title, Text } = Typography;

interface InternshipCardProps {
  internship: Internship;
  showControls?: boolean;
  onStatusChange?: (id: number, newStatus: string) => Promise<void>;
}

const statusMap: Record<string, { label: string; color: string }> = {
  sent: { label: 'Отправлено', color: 'blue' },
  accepted: { label: 'Принято', color: 'green' },
  in_progress: { label: 'В процессе', color: 'orange' },
  rejected: { label: 'Отклонено', color: 'red' },
  completed: { label: 'Завершено', color: 'purple' },
  cancelled: { label: 'Отменено', color: 'default' },
};

const InternshipCard: React.FC<InternshipCardProps> = ({
  internship,
  showControls = false,
  onStatusChange,
}) => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);
  const status = statusMap[internship.status] || { label: internship.status, color: 'default' };

  const handleAuthorClick = () => {
    if (internship.artifact?.author_id) {
      navigate(`/profile/author/${internship.artifact.author_id}`);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!onStatusChange) return;
    setLoading(true);
    try {
      await onStatusChange(internship.id, newStatus);
      message.success(`Статус обновлён на "${statusMap[newStatus]?.label || newStatus}"`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка обновления статуса');
    } finally {
      setLoading(false);
    }
  };

  // Действия для партнёра (showControls)
  const actions = [];
  if (showControls && onStatusChange) {
    if (internship.status === 'sent') {
      actions.push(
        <Button key="cancel" size="small" danger onClick={() => handleStatusChange('cancelled')} loading={loading}>
          Отменить
        </Button>
      );
      // Также можно добавить другие кнопки, но они уже есть в PartnerInternships
    }
    // Можно добавить другие кнопки для других статусов, но сейчас ограничимся отменой
  }

  return (
    <Card style={{ marginBottom: 16 }}>
      <Title level={5}>{internship.artifact_title || `Артефакт #${internship.artifact_id}`}</Title>
      <div style={{ marginBottom: 8 }}>
        <span
          onClick={handleAuthorClick}
          style={{
            cursor: internship.artifact?.author_id ? 'pointer' : 'default',
            color: internship.artifact?.author_id ? '#00AEEF' : 'inherit',
            textDecoration: internship.artifact?.author_id ? 'underline' : 'none',
          }}
          onMouseEnter={(e) => { if (internship.artifact?.author_id) e.currentTarget.style.opacity = '0.7'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
        >
          {internship.artifact?.author_name || 'Автор не указан'}
        </span>
        <Text type="secondary" style={{ marginLeft: 16 }}>
          Создано: {new Date(internship.created_at).toLocaleDateString()}
        </Text>
        {internship.response_date && (
          <Text type="secondary" style={{ marginLeft: 16 }}>
            Ответ: {new Date(internship.response_date).toLocaleDateString()}
          </Text>
        )}
      </div>
      <div style={{ marginTop: 8 }}>
        <Tag color={status.color}>{status.label}</Tag>
      </div>
      {showControls && actions.length > 0 && (
        <Space style={{ marginTop: 12 }}>
          {actions}
        </Space>
      )}
    </Card>
  );
};

export default InternshipCard;