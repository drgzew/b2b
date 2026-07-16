import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Popconfirm } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import ArtifactCard from '../../components/ArtifactCard';
import type { Favorite } from '../../api/types';

const { Title, Text } = Typography;

const PartnerFavorites: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<Favorite[]>([]);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const res = await partnerAPI.getFavorites();
      setFavorites(res.data || []);
    } catch (error) {
      message.error('Не удалось загрузить избранное');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (favoriteId: number) => {
    try {
      await partnerAPI.removeFavorite(favoriteId);
      message.success('Удалено из избранного');
      await fetchFavorites();
    } catch (error) {
      message.error('Ошибка удаления');
    }
  };

  const handleRequestFullText = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'full_text' });
      message.success('Запрос на полный текст отправлен куратору');
    } catch (error: any) {
      const detail: string = error.response?.data?.detail || '';
      // Текст уже доступен — не ошибка: сразу открываем документ.
      if (error.response?.status === 400 && detail.includes('already accessible')) {
        message.info('Полный текст уже доступен — открываю документ');
        await handleRead(artifactId);
        return;
      }
      message.error(detail || 'Ошибка');
    }
  };

  // Приглашение на стажировку — отдельная сущность Internship (не Request):
  // так оно появится и на странице стажировок партнёра, и у автора.
  const handleInternship = async (artifactId: number) => {
    try {
      await partnerAPI.createInternship(artifactId, '');
      message.success('Приглашение на стажировку отправлено');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  // Открытие полного текста (см. PartnerDigest.handleRead: окно открывается
  // синхронно до await, иначе браузер блокирует popup)
  const handleRead = async (artifactId: number) => {
    const win = window.open('', '_blank');
    try {
      const res = await partnerAPI.getReadAccess(artifactId);
      if (res.data.url) {
        if (win) {
          win.location.href = res.data.url;
        } else {
          window.open(res.data.url, '_blank', 'noopener');
        }
      } else {
        win?.close();
        message.warning('Ссылка на документ не указана');
      }
    } catch (error: any) {
      win?.close();
      message.error(error.response?.data?.detail || 'Доступ к тексту ещё не выдан');
    }
  };

  const handleSaveFavorite = async (artifactId: number) => {
    try {
      await partnerAPI.addFavorite(artifactId);
      message.success('Добавлено в избранное');
      await fetchFavorites();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>⭐ Избранные артефакты</Title>
        <Button onClick={() => navigate('/partner/dashboard')}>← На дашборд</Button>
      </div>

      {favorites.length > 0 && (
        <Card style={{ marginBottom: 24, background: '#fff7e6', borderColor: '#faad14' }}>
          <Text strong style={{ fontSize: 16, color: '#faad14' }}>
            Всего в избранном: {favorites.length} артефактов
          </Text>
        </Card>
      )}

      {favorites.length === 0 ? (
        <Card>
          <Empty description="Вы пока ничего не добавили в избранное">
            <Button type="primary" style={{ background: '#00AEEF' }} onClick={() => navigate('/partner/digest')}>
              Перейти к дайджесту
            </Button>
          </Empty>
        </Card>
      ) : (
        favorites.map(fav => (
          <Card
            key={fav.id}
            style={{ marginBottom: 16, position: 'relative' }}
            extra={
              <Popconfirm
                title="Удалить из избранного?"
                description="Это действие нельзя отменить"
                onConfirm={() => handleRemoveFavorite(fav.id)}
                okText="Да"
                cancelText="Нет"
              >
                <Button type="text" danger>✕ Удалить</Button>
              </Popconfirm>
            }
          >
            <ArtifactCard
              artifact={fav.artifact}
              canRead={fav.artifact.read_policy === 'open'}
              onRead={handleRead}
              onRequestFullText={handleRequestFullText}
              onInternship={handleInternship}
              onSaveFavorite={handleSaveFavorite}
              onRemoveFavorite={handleRemoveFavorite}
              isFavorite={true}
              favoriteId={fav.id}
            />
          </Card>
        ))
      )}
    </div>
  );
};

export default PartnerFavorites;