import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, message, Tag, Select } from 'antd';
import { useNavigate } from 'react-router-dom';
import { authorAPI } from '../../api/author';
import type { Artifact } from '../../api/types';

const { Title, Text } = Typography;

const AuthorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [authorName, setAuthorName] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const meRes = await authorAPI.getMe();
      setJobStatus(meRes.data.job_status);
      setAuthorName(meRes.data.full_name);
      const artsRes = await authorAPI.getArtifacts();
      setArtifacts(artsRes.data || []);
    } catch (error) {
      message.error('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  const handleJobStatusChange = async (status: string) => {
    try {
      await authorAPI.updateJobStatus(status);
      setJobStatus(status);
      message.success('Статус обновлён');
    } catch (error) {
      message.error('Ошибка обновления статуса');
    }
  };

  const handleReadPolicyChange = async (artifactId: number, policy: 'open' | 'requires_approval') => {
    try {
      await authorAPI.updateReadPolicy(artifactId, policy);
      await fetchData();
      message.success('Политика доступа обновлена');
    } catch (error) {
      message.error('Ошибка обновления политики');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <Title level={4}>Кабинет автора{authorName ? ` — ${authorName}` : ''}</Title>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Text strong>Статус трудоустройства:</Text>
          <Select
            value={jobStatus}
            onChange={handleJobStatusChange}
            options={[
              { value: 'searching', label: 'Ищет работу' },
              { value: 'not_searching', label: 'Не ищет' },
              { value: 'employed', label: 'Работает' },
            ]}
          />
        </div>
      </Card>

      <Title level={5}>Мои работы</Title>
      {artifacts.length === 0 ? (
        <Card>
          <Text type="secondary">У вас пока нет артефактов</Text>
        </Card>
      ) : (
        artifacts.map((art) => (
          <Card key={art.id} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Title level={5}>{art.title}</Title>
                <Tag color="#00AEEF">{art.type}</Tag>
                <Tag color={art.curator_status === 'approved' ? 'green' : 'orange'}>
                  {art.curator_status}
                </Tag>
                <div style={{ marginTop: 8 }}>
                  <Text strong>Политика доступа:</Text>
                  <Select
                    value={art.read_policy}
                    onChange={(val) => handleReadPolicyChange(art.id, val)}
                    style={{ marginLeft: 8, width: 180 }}
                    options={[
                      { value: 'open', label: 'Открыт для всех' },
                      { value: 'requires_approval', label: 'Требует одобрения' },
                    ]}
                  />
                </div>
              </div>
              <Button onClick={() => navigate(`/profile/author/${art.author_id}`)}>Профиль</Button>
            </div>
          </Card>
        ))
      )}

      <div style={{ marginTop: 24 }}>
        <Button type="primary" onClick={() => navigate('/author/requests')}>
          Запросы на полный текст
        </Button>
      </div>
    </div>
  );
};

export default AuthorDashboard;