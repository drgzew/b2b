import React, { useState, useEffect, useMemo } from 'react';
import { Card, Typography, Button, Tag, Checkbox, Select, Input, Spin, Empty, message } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import type { Subscription, DigestEntry } from '../../api/types';
import ArtifactCard from '../../components/ArtifactCard';

const { Title, Text } = Typography;

const PartnerDigest: React.FC = () => {
  const { subscriptionId } = useParams<{ subscriptionId: string }>();
  const navigate = useNavigate();
  const topicIdNum = subscriptionId ? parseInt(subscriptionId) : undefined;

  const [loading, setLoading] = useState(true);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [entries, setEntries] = useState<DigestEntry[]>([]);
  const [filterTopicId, setFilterTopicId] = useState<number | undefined>(topicIdNum);
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    partnerAPI.getSubscriptions()
      .then(res => setSubscriptions(res.data))
      .catch(() => message.error('Не удалось загрузить подписки'));
  }, []);

  useEffect(() => {
    if (filterTopicId) {
      loadDigestForTopic(filterTopicId);
    } else {
      loadAllDigests(subscriptions);
    }
  }, [filterTopicId, subscriptions]);

  const loadDigestForTopic = async (id: number) => {
    setLoading(true);
    try {
      const res = await partnerAPI.getDigest(id);
      setEntries(res.data);
    } catch (error) {
      message.error('Не удалось загрузить дайджест для темы');
    } finally {
      setLoading(false);
    }
  };

  const loadAllDigests = async (subs: Subscription[]) => {
    setLoading(true);
    try {
      const byId = new Map<number, DigestEntry>();
      for (const sub of subs) {
        try {
          const res = await partnerAPI.getDigest(sub.id);
          res.data.forEach(entry => {
            const existing = byId.get(entry.artifact.id);
            if (!existing || entry.relevance > existing.relevance) {
              byId.set(entry.artifact.id, entry);
            }
          });
        } catch {
          // пропускаем
        }
      }
      setEntries(Array.from(byId.values()));
    } catch (error) {
      message.error('Не удалось загрузить дайджесты');
    } finally {
      setLoading(false);
    }
  };

  const availableTags = useMemo(() => {
    const map = new Map<number, { id: number; name: string }>();
    entries.forEach(e => e.artifact.tags.forEach(t => {
      if (!map.has(t.id)) map.set(t.id, t);
    }));
    return Array.from(map.values());
  }, [entries]);

  const filteredEntries = useMemo(() => {
    let result = entries;
    if (selectedTagIds.length > 0) {
      result = result.filter(e =>
        e.artifact.tags.some(t => selectedTagIds.includes(t.id))
      );
    }
    if (searchText.trim()) {
      const s = searchText.toLowerCase().trim();
      result = result.filter(e =>
        e.artifact.title.toLowerCase().includes(s) ||
        e.artifact.annotation.toLowerCase().includes(s) ||
        e.artifact.tags.some(t => t.name.toLowerCase().includes(s))
      );
    }
    return result;
  }, [entries, selectedTagIds, searchText]);

  const handleTagToggle = (tagId: number) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId) ? prev.filter(id => id !== tagId) : [...prev, tagId]
    );
  };

  const handleRequestFullText = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'full_text' });
      message.success('Запрос на полный текст отправлен куратору');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка отправки запроса');
    }
  };

  const handleInternship = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'internship' });
      message.success('Приглашение на стажировку отправлено');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка отправки приглашения');
    }
  };

  const handleSaveFavorite = async (artifactId: number) => {
    try {
      await partnerAPI.addFavorite(artifactId);
      message.success('Добавлено в избранное');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;

  const currentSub = subscriptions.find(s => s.id === filterTopicId);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>Дайджест {currentSub ? `: ${currentSub.name}` : '(все подписки)'}</Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <Text strong>Тема:</Text>
            <Select
              style={{ width: '100%', marginTop: 4 }}
              placeholder="Все темы"
              allowClear
              value={filterTopicId}
              onChange={setFilterTopicId}
              options={subscriptions.map(s => ({ label: s.name, value: s.id }))}
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

      {filteredEntries.length === 0 ? (
        <Card><Empty description="Пока нет релевантных работ по этой подписке" /></Card>
      ) : (
        filteredEntries.map(entry => (
          <ArtifactCard
            key={entry.artifact.id}
            artifact={entry.artifact}
            relevance={entry.relevance}
            onRequestFullText={handleRequestFullText}
            onInternship={handleInternship}
            onSaveFavorite={handleSaveFavorite}
          />
        ))
      )}
    </div>
  );
};

export default PartnerDigest;