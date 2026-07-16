import React from 'react';
import { Card, Typography, Button, Tag, Space, Progress, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { Artifact } from '../api/types';

const { Title, Paragraph, Text } = Typography;

interface ArtifactCardProps {
  artifact: Artifact;
  relevance?: number;
  canRead?: boolean; // ✅ добавлено: доступен ли полный текст для чтения
  onRequestFullText: (artifactId: number) => void;
  onInternship: (artifactId: number) => void;
  onSaveFavorite: (artifactId: number) => void;
  onRemoveFavorite?: (favoriteId: number) => void;
  isFavorite?: boolean;
  favoriteId?: number;
}

const formatType = (type: string) => {
  const map: Record<string, string> = { vkr: 'ВКР', article: 'Статья', talk: 'Доклад', event: 'Событие' };
  return map[type] || type;
};

const getYear = (dateStr: string) => new Date(dateStr).getFullYear();

const ArtifactCard: React.FC<ArtifactCardProps> = ({
  artifact,
  relevance,
  canRead = false,
  onRequestFullText,
  onInternship,
  onSaveFavorite,
  onRemoveFavorite,
  isFavorite = false,
  favoriteId,
}) => {
  const navigate = useNavigate();

  const handleAuthorClick = () => {
    if (artifact.author_id) navigate(`/profile/author/${artifact.author_id}`);
  };

  const handleSupervisorClick = () => {
    if (artifact.supervisor_id) navigate(`/profile/teacher/${artifact.supervisor_id}`);
  };

  const handleFavoriteToggle = () => {
    if (isFavorite && onRemoveFavorite && favoriteId) {
      onRemoveFavorite(favoriteId);
    } else {
      onSaveFavorite(artifact.id);
    }
  };

  const relevancePercent = relevance !== undefined ? Math.round(relevance * 100) : undefined;

  // ✅ Основная логика кнопки «Запросить полный текст»
  const handleRead = () => {
    if (canRead) {
      // Если доступ уже есть — открываем файл
      if (artifact.file_path) {
        // Для ВКР — редирект, для статьи/доклада — открыть PDF в новой вкладке
        if (artifact.type === 'vkr') {
          window.location.href = artifact.file_path;
        } else {
          window.open(artifact.file_path, '_blank');
        }
      } else {
        message.warning('Файл недоступен');
      }
    } else {
      // Нет доступа — отправляем запрос
      onRequestFullText(artifact.id);
    }
  };

  return (
    <Card style={{ marginBottom: 16 }}>
      <Title level={5}>{artifact.title}</Title>

      <div style={{ marginBottom: 8 }}>
        <span
          onClick={handleAuthorClick}
          style={{
            cursor: artifact.author_id ? 'pointer' : 'default',
            color: artifact.author_id ? '#00AEEF' : 'inherit',
            textDecoration: artifact.author_id ? 'underline' : 'none',
          }}
          onMouseEnter={(e) => { if (artifact.author_id) e.currentTarget.style.opacity = '0.7'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
        >
          {artifact.author_name || 'Автор не указан'}
        </span>
        <Text type="secondary" style={{ marginLeft: 16 }}>{getYear(artifact.created_at)}</Text>
        <Tag color="#00AEEF" style={{ marginLeft: 16 }}>{formatType(artifact.type)}</Tag>
        {artifact.supervisor_name && (
          <>
            <Text type="secondary" style={{ marginLeft: 8 }}>Научный руководитель: </Text>
            <span
              onClick={handleSupervisorClick}
              style={{
                cursor: artifact.supervisor_id ? 'pointer' : 'default',
                color: artifact.supervisor_id ? '#00AEEF' : 'inherit',
                textDecoration: artifact.supervisor_id ? 'underline' : 'none',
              }}
              onMouseEnter={(e) => { if (artifact.supervisor_id) e.currentTarget.style.opacity = '0.7'; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
            >
              {artifact.supervisor_name}
            </span>
          </>
        )}
      </div>

      <div style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {artifact.tags.map((tag) => (
          <Tag key={tag.id} color="#e6f0fa" style={{ color: '#1a2a3a' }}>{tag.name}</Tag>
        ))}
      </div>

      <Paragraph ellipsis={{ rows: 3 }}>{artifact.annotation}</Paragraph>

      {relevancePercent !== undefined && (
        <div style={{ marginTop: 8, marginBottom: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>Релевантность: {relevancePercent}%</Text>
          <Progress
            percent={relevancePercent}
            size="small"
            status={relevancePercent >= 80 ? 'success' : 'active'}
            strokeColor={relevancePercent >= 80 ? '#52c41a' : '#00AEEF'}
            showInfo={false}
            style={{ width: 150 }}
          />
        </div>
      )}

      <Space>
        <Button
          type="primary"
          style={{ background: '#00AEEF' }}
          onClick={handleRead}  // ✅ теперь используется новая логика
        >
          {canRead ? '📄 Открыть полный текст' : '📩 Запросить полный текст'}
        </Button>
        <Button onClick={() => onInternship(artifact.id)}>
          💼 Пригласить на стажировку
        </Button>
        <Button
          type="text"
          onClick={handleFavoriteToggle}
          style={{ color: isFavorite ? '#faad14' : undefined }}
        >
          {isFavorite ? '⭐' : '☆'}
        </Button>
      </Space>
    </Card>
  );
};

export default ArtifactCard;