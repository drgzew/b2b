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
  const [partnerName, setPartnerName] = useState<string>('');
  const [internshipCount, setInternshipCount] = useState(0);
  const [favoriteCount, setFavoriteCount] = useState(0);

  useEffect(() => {
    const fetchPartnerData = async () => {
      // 1. Получаем имя партнёра (обязательно)
      try {
        const partnerResponse = await partnerAPI.getMe();
        setPartnerName(partnerResponse.data.name);
      } catch (error) {
        console.error('Ошибка получения имени партнёра:', error);
        setPartnerName('Партнёр');
      }

      // 2. Получаем количество стажировок (если эндпоинт не готов — просто ставим 0)
      try {
        const internshipsResponse = await partnerAPI.getInternships();
        setInternshipCount(internshipsResponse.data?.length || 0);
      } catch (error) {
        console.warn('Не удалось загрузить стажировки:', error);
        setInternshipCount(0); // не сбрасываем имя
      }

      // 3. Получаем количество избранных (если эндпоинт не готов — просто ставим 0)
      try {
        const favoritesResponse = await partnerAPI.getFavorites();
        setFavoriteCount(favoritesResponse.data?.length || 0);
      } catch (error) {
        console.warn('Не удалось загрузить избранное:', error);
        setFavoriteCount(0); // не сбрасываем имя
      }
    };

    fetchPartnerData();
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
              style={{
                backgroundColor: '#00AEEF',
                color: '#fff',
                marginLeft: '8px',
              }}
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
              style={{
                backgroundColor: '#faad14',
                color: '#fff',
                marginLeft: '8px',
              }}
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