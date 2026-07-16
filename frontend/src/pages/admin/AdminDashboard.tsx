import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Statistic, Spin, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../../api/admin';

const { Title, Text } = Typography;

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [usersCount, setUsersCount] = useState(0);
  const [partnersCount, setPartnersCount] = useState(0);

  useEffect(() => {
    Promise.all([adminAPI.getUsers(), adminAPI.getPartners()])
      .then(([usersRes, partnersRes]) => {
        setUsersCount(usersRes.data.length);
        setPartnersCount(partnersRes.data.length);
      })
      .catch(() => message.error('Не удалось загрузить сводку'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={3}>Панель администратора</Title>
      <Text type="secondary">
        Управление пользователями, партнёрами и загрузка данных из парсера.
      </Text>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card hoverable onClick={() => navigate('/admin/users')}>
            <Statistic title="Пользователей" value={usersCount} />
          </Card>
        </Col>
        <Col span={8}>
          <Card hoverable onClick={() => navigate('/admin/partners')}>
            <Statistic title="Партнёров" value={partnersCount} />
          </Card>
        </Col>
        <Col span={8}>
          <Card hoverable onClick={() => navigate('/admin/import')}>
            <Text strong>Импорт данных из парсера →</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdminDashboard;
