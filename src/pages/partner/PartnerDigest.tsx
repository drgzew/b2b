import React, { useState, useMemo } from 'react';
import { Card, Typography, Button, Tag, Space, Checkbox, Select, Input } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { topics } from '../../mocks/topics';
import { artifacts } from '../../mocks/artifacts';

const { Title, Paragraph, Text } = Typography;

const hasCommonTag = (artifactTags: any[], topicTags: any[]) => {
  const artifactTagIds = artifactTags.map(t => t.id);
  const topicTagIds = topicTags.map(t => t.id);
  return artifactTagIds.some(id => topicTagIds.includes(id));
};

const PartnerDigest: React.FC = () => {
  const { topicId } = useParams<{ topicId: string }>();
  const navigate = useNavigate();
  const topicIdNum = topicId ? parseInt(topicId) : undefined;

  const savedSubscriptions = localStorage.getItem('partner_subscriptions');
  const selectedTopicIds: number[] = savedSubscriptions ? JSON.parse(savedSubscriptions) : [1, 2];

  const subscribedTopics = topics.filter(t => selectedTopicIds.includes(t.id));

  const currentTopic = topicIdNum ? topics.find(t => t.id === topicIdNum) : undefined;

  const [filterTopicId, setFilterTopicId] = useState<number | undefined>(topicIdNum);
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const [searchText, setSearchText] = useState('');

  const allMatchedArtifacts = useMemo(() => {
    const matched = artifacts.filter(art =>
      subscribedTopics.some(topic => hasCommonTag(art.tags, topic.tags))
    );
    return matched;
  }, [subscribedTopics]);

  const artifactsByTopic = useMemo(() => {
    if (filterTopicId) {
      const topic = topics.find(t => t.id === filterTopicId);
      if (!topic) return allMatchedArtifacts;
      return allMatchedArtifacts.filter(art => hasCommonTag(art.tags, topic.tags));
    }
    return allMatchedArtifacts;
  }, [allMatchedArtifacts, filterTopicId]);

const availableTags = useMemo(() => {
  const tagSet = new Set<number>();
  artifactsByTopic.forEach(art => art.tags.forEach(t => tagSet.add(t.id)));
  const result: { id: number; name: string }[] = [];
  for (const id of tagSet) {
    let found = false;
    for (const topic of topics) {
      const tag = topic.tags.find(t => t.id === id);
      if (tag) {
        result.push(tag);
        found = true;
        break;
      }
    }
  }
  return result;
}, [artifactsByTopic]);
  const filteredArtifacts = useMemo(() => {
    let result = artifactsByTopic;

    if (selectedTagIds.length > 0) {
      result = result.filter(art =>
        art.tags.some(t => selectedTagIds.includes(t.id))
      );
    }

    if (searchText.trim()) {
      const s = searchText.toLowerCase().trim();
      result = result.filter(art =>
        art.title.toLowerCase().includes(s) ||
        art.annotation.toLowerCase().includes(s) ||
        art.tags.some(t => t.name.toLowerCase().includes(s))
      );
    }

    return result;
  }, [artifactsByTopic, selectedTagIds, searchText]);

  const handleTagToggle = (tagId: number) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId) ? prev.filter(id => id !== tagId) : [...prev, tagId]
    );
  };

  const formatType = (type: string) => {
    if (type === 'vkr') return 'ВКР';
    if (type === 'article') return 'Статья';
    return type;
  };

  const getYear = (createdAt: string) => new Date(createdAt).getFullYear();

  const handleTopicFilterChange = (value: number | undefined) => {
    setFilterTopicId(value);
    if (value) {
      navigate(`/partner/digest/${value}`, { replace: true });
    } else {
      navigate('/partner/digest', { replace: true });
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>
          Дайджест {currentTopic ? `: ${currentTopic.name}` : '(все подписки)'}
        </Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      {/* Фильтры */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <Text strong>Тема:</Text>
            <Select
              style={{ width: '100%', marginTop: 4 }}
              placeholder="Все темы"
              allowClear
              value={filterTopicId}
              onChange={handleTopicFilterChange}
              options={subscribedTopics.map(t => ({ label: t.name, value: t.id }))}
            />
          </div>
          <div style={{ flex: 2, minWidth: 200 }}>
            <Text strong>Поиск:</Text>
            <Input
              placeholder="Поиск по названию, аннотации, тегам..."
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              style={{ marginTop: 4 }}
            />
          </div>
        </div>

        {availableTags.length > 0 && (
          <div>
            <Text strong>Фильтр по тегам:</Text>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <Checkbox
                checked={selectedTagIds.length === availableTags.length}
                indeterminate={selectedTagIds.length > 0 && selectedTagIds.length < availableTags.length}
                onChange={() => {
                  if (selectedTagIds.length === availableTags.length) {
                    setSelectedTagIds([]);
                  } else {
                    setSelectedTagIds(availableTags.map(t => t.id));
                  }
                }}
              >
                Все
              </Checkbox>
              {availableTags.map(tag => (
                <Checkbox
                  key={tag.id}
                  checked={selectedTagIds.includes(tag.id)}
                  onChange={() => handleTagToggle(tag.id)}
                >
                  <Tag color={selectedTagIds.includes(tag.id) ? '#00AEEF' : undefined}>
                    {tag.name}
                  </Tag>
                </Checkbox>
              ))}
            </div>
          </div>
        )}
      </Card>

      {filteredArtifacts.length === 0 ? (
        <Card>
          <Text type="secondary">Нет артефактов, соответствующих фильтрам</Text>
        </Card>
      ) : (
        filteredArtifacts.map(art => (
          <Card key={art.id} style={{ marginBottom: 16 }}>
            <Title level={5}>{art.title}</Title>
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary">{art.author_name}</Text>
              <Text type="secondary" style={{ marginLeft: 16 }}>{getYear(art.created_at)}</Text>
              <Tag color="#00AEEF" style={{ marginLeft: 16 }}>{formatType(art.type)}</Tag>
            </div>
            <div style={{ marginBottom: 12 }}>
              {art.tags.map(tag => (
                <Tag key={tag.id} color="#e6f0fa" style={{ color: '#1a2a3a' }}>{tag.name}</Tag>
              ))}
            </div>
            <Paragraph ellipsis={{ rows: 3 }}>{art.annotation}</Paragraph>
            <Space>
              <Button type="primary" style={{ background: '#00AEEF' }}>📩 Запросить полный текст</Button>
              <Button>⭐ Сохранить в избранное</Button>
            </Space>
          </Card>
        ))
      )}
    </div>
  );
};

export default PartnerDigest;