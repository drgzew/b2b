import React from 'react';
import { Card, Typography, Button, Space } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const AdminPanel: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <Title level={3}>Панель администратора</Title>
      <Card style={{ marginBottom: 16 }}>
        <Text>
          Добро пожаловать в панель администратора. Здесь вы можете управлять пользователями, 
          партнёрами и контентом.
        </Text>
        <div style={{ marginTop: 16 }}>
          <Space>
            <Button type="primary" onClick={() => navigate('/admin/users')}>
              Пользователи
            </Button>
            <Button onClick={() => navigate('/admin/partners')}>
              Партнёры
            </Button>
            <Button onClick={() => navigate('/admin/artifacts')}>
              Артефакты
            </Button>
          </Space>
        </div>
      </Card>
      <Button onClick={() => navigate(-1)}>Назад</Button>
    </div>
  );
};

export default AdminPanel;