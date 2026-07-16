import React, { useState, useEffect } from 'react';
import { Layout, Badge } from 'antd';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';
import { partnerAPI } from '../api/partner';

const { Content } = Layout;

interface PartnerLayoutProps {
  children?: React.ReactNode;
}

const PartnerLayout: React.FC<PartnerLayoutProps> = ({ children }) => {
  const [partnerName, setPartnerName] = useState('');
  const [internshipCount, setInternshipCount] = useState(0);
  const [favoriteCount, setFavoriteCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const me = await partnerAPI.getMe();
        setPartnerName(me.data.name);
      } catch (e) {}

      try {
        const internships = await partnerAPI.getInternships();
        setInternshipCount(internships.data.length);
      } catch (e) {}

      try {
        const favorites = await partnerAPI.getFavorites();
        setFavoriteCount(favorites.data.length);
      } catch (e) {}
    };
    fetchData();
  }, []);

  const menuItems = [
    { label: 'Дашборд', path: '/partner/dashboard' },
    { label: 'Подписки', path: '/partner/digest' },
    {
      label: (
        <span>
          💼 Стажировки
          {internshipCount > 0 && (
            <Badge
              count={internshipCount}
              style={{ backgroundColor: '#00AEEF', color: '#fff', marginLeft: 8 }}
            />
          )}
        </span>
      ),
      path: '/partner/internships',
    },
    {
      label: (
        <span>
          ⭐ Избранное
          {favoriteCount > 0 && (
            <Badge
              count={favoriteCount}
              style={{ backgroundColor: '#faad14', color: '#fff', marginLeft: 8 }}
            />
          )}
        </span>
      ),
      path: '/partner/favorites',
    },
  ];

  const title = partnerName ? `Кабинет партнёра - ${partnerName}` : 'Кабинет партнёра';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header title={title} menuItems={menuItems} />
      <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280, background: '#fff', borderRadius: 8 }}>
        {children ? children : <Outlet />}
      </Content>
    </Layout>
  );
};

export default PartnerLayout;