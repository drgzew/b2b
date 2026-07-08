import React, { useState, useMemo } from 'react';
import { Row, Col, Card, Typography, Badge, Tag, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { topics } from '../../mocks/topics';
import { artifacts } from '../../mocks/artifacts';
import SubscriptionManager from '../../components/SubscriptionManager';

const { Title, Text } = Typography;

const hasCommonTag = (artifactTags: any[], topicTags: any[]) => {
  const artifactTagIds = artifactTags.map(t => t.id);
  const topicTagIds = topicTags.map(t => t.id);
  return artifactTagIds.some(id => topicTagIds.includes(id));
};

const PartnerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [isManagerVisible, setManagerVisible] = useState(false);

  const savedSubscriptions = localStorage.getItem('partner_subscriptions');
  const [selectedTopicIds, setSelectedTopicIds] = useState<number[]>(
    savedSubscriptions ? JSON.parse(savedSubscriptions) : [1, 2]
  );

  const getArtifactCount = (topicId: number) => {
    const topic = topics.find(t => t.id === topicId);
    if (!topic) return 0;
    return artifacts.filter(art => hasCommonTag(art.tags, topic.tags)).length;
  };

  const totalNewWorks = useMemo(() => {
    let sum = 0;
    selectedTopicIds.forEach(topicId => {
      const topic = topics.find(t => t.id === topicId);
      if (!topic) return;
      sum += artifacts.filter(art => hasCommonTag(art.tags, topic.tags)).length;
    });
    return sum;
  }, [selectedTopicIds]);

  const selectedTopics = topics.filter(t => selectedTopicIds.includes(t.id));

  const handleSaveSubscriptions = (newTopicIds: number[]) => {
    setSelectedTopicIds(newTopicIds);
    localStorage.setItem('partner_subscriptions', JSON.stringify(newTopicIds));
    message.success('Подписки обновлены');
  };

  return (
    <div className="page-container">
      <Badge.Ribbon text="Новые" color="#00AEEF">
        <Card style={{ marginBottom: 32, background: '#f0f7ff', borderColor: '#00AEEF' }}>
          <Title level={4} style={{ margin: 0 }}>
            На этой неделе — <span style={{ color: '#00AEEF' }}>{totalNewWorks}</span> новых работ
          </Title>
          <Text type="secondary">по вашим подпискам</Text>
        </Card>
      </Badge.Ribbon>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>Ваши подписки</Title>
        <Button type="primary" style={{ background: '#00AEEF' }} onClick={() => setManagerVisible(true)}>
          ✏️ Управление подписками
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {selectedTopics.map((topic) => {
          const count = getArtifactCount(topic.id);
          console.log('Topic tags:', topic.tags);
          return (
            <Col key={topic.id} xs={24} sm={12} lg={8}>
              <Card
                hoverable
                title={topic.name}
                extra={<Text type="secondary">{count} работ</Text>}
                style={{ borderColor: '#00AEEF', borderWidth: 1, height: '100%' }}
                onClick={() => navigate(`/partner/digest/${topic.id}`)}
              >
                <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {topic.tags && topic.tags.length > 0 ? (
                    topic.tags.map(tag => (
                      <Tag key={tag.id} color="#1a2a3a">
                        {tag.name || '?'}
                      </Tag>
                    ))
                  ) : (
                    <Text type="secondary" style={{ fontSize: 12 }}>Нет тегов</Text>
                  )}
                </div>
                <Text>{topic.description}</Text>
              </Card>
            </Col>
          );
        })}
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
