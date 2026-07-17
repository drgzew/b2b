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
  const [selectedTagNames, setSelectedTagNames] = useState<string[]>([]);
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

  const currentSub = subscriptions.find(s => s.id === filterTopicId);

  const availableTags = useMemo(() => {
    if (filterTopicId && currentSub) {
      // Конкретная подписка – берём её теги
      return (currentSub.tags || []).map((t: string | { id: number; name: string }) =>
        typeof t === 'string' ? t : t.name
      );
    } else {
      // Все подписки – собираем уникальные теги из всех подписок
      const tagSet = new Set<string>();
      subscriptions.forEach(sub => {
        (sub.tags || []).forEach((t: string | { id: number; name: string }) => {
          const name = typeof t === 'string' ? t : t.name;
          tagSet.add(name);
        });
      });
      return Array.from(tagSet);
    }
  }, [filterTopicId, currentSub, subscriptions]);

  const filteredEntries = useMemo(() => {
    let result = entries;
    if (selectedTagNames.length > 0) {
      result = result.filter(e =>
        e.artifact.tags.some((t: string | { id: number; name: string }) => {
          const name = typeof t === 'string' ? t : t.name;
          return selectedTagNames.includes(name);
        })
      );
    }
    if (searchText.trim()) {
      const s = searchText.toLowerCase().trim();
      result = result.filter(e =>
        e.artifact.title.toLowerCase().includes(s) ||
        e.artifact.annotation.toLowerCase().includes(s) ||
        e.artifact.tags.some((t: string | { id: number; name: string }) => {
          const name = typeof t === 'string' ? t : t.name;
          return name.toLowerCase().includes(s);
        })
      );
    }
    return result;
  }, [entries, selectedTagNames, searchText]);

  const handleTagToggle = (tagName: string) => {
    setSelectedTagNames(prev =>
      prev.includes(tagName) ? prev.filter(n => n !== tagName) : [...prev, tagName]
    );
  };

  // Открытие полного текста: бэкенд отдаёт ссылку на документ, если работа в
  // открытом доступе или доступ уже выдан по одобренному запросу.
  // Вкладку открываем синхронно (до await) — иначе браузер заблокирует
  // window.open как popup, т.к. он окажется вне обработчика клика.
  const handleRead = async (artifactId: number) => {
    const win = window.open('', '_blank');
    try {
      const res = await partnerAPI.getReadAccess(artifactId);
      if (res.data.url) {
        if (win) {
          win.location.href = res.data.url;
        } else {
          window.open(res.data.url, '_blank', 'noopener');
        }
      } else {
        win?.close();
        message.warning('Ссылка на документ не указана');
      }
    } catch (error: any) {
      win?.close();
      message.error(error.response?.data?.detail || 'Доступ к тексту ещё не выдан');
    }
  };

  const handleRequestFullText = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'full_text' });
      message.success('Запрос на полный текст отправлен куратору');
    } catch (error: any) {
      const detail: string = error.response?.data?.detail || '';
      // Текст уже доступен (автор открыл работу или доступ выдан по прошлому
      // запросу) — это не ошибка: открываем документ и обновляем карточку.
      if (error.response?.status === 400 && detail.includes('already accessible')) {
        message.info('Полный текст уже доступен — открываю документ');
        setEntries(prev =>
          prev.map(e => (e.artifact.id === artifactId ? { ...e, can_read: true } : e))
        );
        await handleRead(artifactId);
        return;
      }
      message.error(detail || 'Ошибка отправки запроса');
    }
  };

  const handleInternship = async (artifactId: number) => {
    try {
      await partnerAPI.createInternship(
        artifactId,
        ""
      );

      message.success('Приглашение на стажировку отправлено');
    } catch (error: any) {
      message.error(
        error.response?.data?.detail || 'Ошибка отправки приглашения'
      );
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
                checked={selectedTagNames.length === availableTags.length}
                indeterminate={selectedTagNames.length > 0 && selectedTagNames.length < availableTags.length}
                onChange={() => {
                  if (selectedTagNames.length === availableTags.length) {
                    setSelectedTagNames([]);
                  } else {
                    setSelectedTagNames(availableTags);
                  }
                }}
              >
                Все
              </Checkbox>

              {availableTags.map(tagName => (
                <Checkbox
                  key={tagName}
                  checked={selectedTagNames.includes(tagName)}
                  onChange={() => handleTagToggle(tagName)}
                >
                  <Tag color={selectedTagNames.includes(tagName) ? '#00AEEF' : undefined}>
                    {tagName}
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
            canRead={entry.can_read}
            onRead={handleRead}
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