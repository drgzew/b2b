import React, { useState, useEffect, useMemo } from 'react';
import { Row, Col, Card, Typography, Badge, Tag, Button, message, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import type { Subscription } from '../../api/types';
import SubscriptionManager from '../../components/SubscriptionManager';
import { topics } from '../../mocks/topics';
import { plural } from '../../utils/plural';

const { Title, Text } = Typography;

const PartnerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [subscriptionCounts, setSubscriptionCounts] = useState<Record<number, number>>({});
  const [totalNewWorks, setTotalNewWorks] = useState(0);
  const [isManagerVisible, setManagerVisible] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const subsRes = await partnerAPI.getSubscriptions();
      const subs = subsRes.data || [];
      setSubscriptions(subs);

      const counts: Record<number, number> = {};
      let total = 0;
      for (const sub of subs) {
        try {
          const digestRes = await partnerAPI.getDigest(sub.id);
          const count = digestRes.data.length;
          counts[sub.id] = count;
          total += count;
        } catch {
          counts[sub.id] = 0;
        }
      }
      setSubscriptionCounts(counts);
      setTotalNewWorks(total);
    } catch (error) {
      message.error('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  const selectedTopicIds = useMemo(() => {
    return subscriptions
      .map(sub => topics.find(t => t.name === sub.name)?.id)
      .filter((id): id is number => id !== undefined);
  }, [subscriptions]);

  const handleSaveSubscriptions = async (newTopicIds: number[]) => {
    const chosen = topics.filter(t => newTopicIds.includes(t.id));
    try {
      await partnerAPI.replaceSubscriptions({
        subscriptions: chosen.map(t => ({
          name: t.name,
          tags: t.tags.map(tag => tag.name),
          description: t.description,
        })),
      });
      message.success('Подписки обновлены');
      await fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось обновить подписки');
      throw error;
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;

  return (
    <div className="page-container">
      <Badge.Ribbon text="Новые" color="#00AEEF">
        <Card style={{ marginBottom: 32, background: '#f0f7ff', borderColor: '#00AEEF' }}>
          <Title level={4}>
            На этой неделе — <span style={{ color: '#00AEEF' }}>{totalNewWorks}</span>{' '}
            {plural(totalNewWorks, 'новая работа', 'новые работы', 'новых работ')}
          </Title>
          <Text type="secondary">по вашим подпискам</Text>
        </Card>
      </Badge.Ribbon>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5}>Ваши подписки</Title>
        <Button type="primary" style={{ background: '#00AEEF' }} onClick={() => setManagerVisible(true)}>
          ✏️ Управление подписками
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {subscriptions.length === 0 ? (
          <Col span={24}><Card><Text type="secondary">У вас пока нет активных подписок</Text></Card></Col>
        ) : (
          subscriptions.map(sub => {
            const count = subscriptionCounts[sub.id] || 0;
            const topic = topics.find(t => t.name === sub.name);
            return (
              <Col key={sub.id} xs={24} sm={12} lg={8}>
                <Card
                  hoverable
                  title={sub.name}
                  extra={<Text type="secondary">{count} {plural(count, 'работа', 'работы', 'работ')}</Text>}
                  style={{ borderColor: '#00AEEF', height: '100%' }}
                  onClick={() => navigate(`/partner/digest/${sub.id}`)}
                >
                  {topic && (
                    <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {topic.tags.slice(0, 6).map(tag => (
                        <Tag key={tag.id} color="#e6f0fa" style={{ color: '#1a2a3a' }}>{tag.name}</Tag>
                      ))}
                      {topic.tags.length > 6 && <Tag>+{topic.tags.length - 6}</Tag>}
                    </div>
                  )}
                  <Text type="secondary">{topic?.description || sub.description || 'Описание отсутствует'}</Text>
                </Card>
              </Col>
            );
          })
        )}
      </Row>

      <SubscriptionManager
        visible={isManagerVisible}
        onClose={() => setManagerVisible(false)}
        onSave={handleSaveSubscriptions}
        selectedTopicIds={selectedTopicIds}
      />
    </div>
  );
};

export default PartnerDashboard;