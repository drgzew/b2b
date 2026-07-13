import React from 'react';
import { Layout } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import Header from '../components/Header';

const { Content } = Layout;

const AuthorLayout: React.FC = () => {
  const navigate = useNavigate();

  const menuItems = [
    { label: 'Мои работы', path: '/author/dashboard' },
    { label: 'Запросы', path: '/author/requests' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header title="Кабинет автора" menuItems={menuItems} />
      <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280, background: '#fff', borderRadius: 8 }}>
        <Outlet />
      </Content>
    </Layout>
  );
};

export default AuthorLayout;