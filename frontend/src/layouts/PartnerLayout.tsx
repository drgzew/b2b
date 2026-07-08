import React from 'react';
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

const { Content } = Layout;

interface PartnerLayoutProps {
  children?: React.ReactNode;
}

const PartnerLayout: React.FC<PartnerLayoutProps> = ({ children }) => {

  const menuItems = [
    { label: 'Дашборд', path: '/partner/dashboard' },
    { label: 'Подписки', path: '/partner/digest' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        title="Кабинет партнёра"
        menuItems={menuItems}
      />
      <Content
        style={{
          margin: '24px 16px',
          padding: 24,
          minHeight: 280,
          background: '#fff',
          borderRadius: 8,
        }}
      >
        {children ? children : <Outlet />}
      </Content>
    </Layout>
  );
};

export default PartnerLayout;