import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';
import { partnerAPI } from '../api/partner';

const { Content } = Layout;

interface PartnerLayoutProps {
  children?: React.ReactNode;
}

const PartnerLayout: React.FC<PartnerLayoutProps> = ({ children }) => {
  const [partnerName, setPartnerName] = useState<string>('');

  useEffect(() => {
    const fetchPartnerName = async () => {
      try {
        const response = await partnerAPI.getMe();
        setPartnerName(response.data.name);
      } catch (error) {
        console.error('Failed to fetch partner info:', error);
        setPartnerName('Партнёр');
      }
    };
    fetchPartnerName();
  }, []);

  const menuItems = [
    { label: 'Дашборд', path: '/partner/dashboard' },
    { label: 'Подписки', path: '/partner/digest' },
  ];

  const title = partnerName ? `Кабинет партнёра - ${partnerName}` : 'Кабинет партнёра';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        title={title}
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