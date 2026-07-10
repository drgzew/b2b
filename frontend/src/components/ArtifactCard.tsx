import React from 'react';
import { Card, Typography, Button, Tag, Space, Progress } from 'antd';
import type { Artifact } from '../api/partner';

const { Title, Paragraph, Text } = Typography;

interface ArtifactCardProps {
  artifact: Artifact;
  relevance?: number; // доля 0..1 из дайджеста; если не задана — шкалу не показываем
  onRequestFullText: (artifactId: number) => void;
  onInternship: (artifactId: number) => void;
  onSaveFavorite: (title: string) => void;
}

const formatType = (type: string) => {
  if (type === 'vkr') return 'ВКР';
  if (type === 'article') return 'Статья';
  if (type === 'talk') return 'Доклад';
  return type;
};

const getYear = (createdAt: string) => new Date(createdAt).getFullYear();

const ArtifactCard: React.FC<ArtifactCardProps> = ({
  artifact,
  relevance,
  onRequestFullText,
  onInternship,
  onSaveFavorite,
}) => {
  // relevance приходит из дайджеста как доля 0..1 (индекс Жаккара) — переводим в проценты.
  const relevancePercent = relevance !== undefined ? Math.round(relevance * 100) : undefined;

  return (
    <Card style={{ marginBottom: 16 }}>
      <Title level={5}>{artifact.title}</Title>
      <div style={{ marginBottom: 8 }}>
        <Text type="secondary">{artifact.author_name || 'Автор не указан'}</Text>
        <Text type="secondary" style={{ marginLeft: 16 }}>{getYear(artifact.created_at)}</Text>
        <Tag color="#00AEEF" style={{ marginLeft: 16 }}>{formatType(artifact.type)}</Tag>
      </div>

      {relevancePercent !== undefined && (
        <div style={{ marginBottom: 12, maxWidth: 260 }}>
          <Text strong style={{ fontSize: 12 }}>Релевантность</Text>
          <Progress
            percent={relevancePercent}
            size="small"
            strokeColor="#00AEEF"
            status={relevancePercent >= 80 ? 'success' : 'active'}
          />
        </div>
      )}

      <div style={{ marginBottom: 12 }}>
        {artifact.tags.map(tag => (
          <Tag key={tag.id} color="#e6f0fa" style={{ color: '#1a2a3a' }}>{tag.name}</Tag>
        ))}
      </div>

      <Paragraph ellipsis={{ rows: 3 }}>{artifact.annotation}</Paragraph>

      <Space>
        <Button
          type="primary"
          style={{ background: '#00AEEF' }}
          onClick={() => onRequestFullText(artifact.id)}
        >
          📩 Запросить полный текст
        </Button>
        <Button onClick={() => onSaveFavorite(artifact.title)}>
          ⭐ Сохранить в избранное
        </Button>
        <Button onClick={() => onInternship(artifact.id)}>
          💼 Пригласить на стажировку
        </Button>
      </Space>
    </Card>
  );
};

export default ArtifactCard;
