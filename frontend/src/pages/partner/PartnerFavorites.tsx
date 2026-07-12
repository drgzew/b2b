import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, Empty, message, Popconfirm } from 'antd';
import { useNavigate } from 'react-router-dom';
import { partnerAPI } from '../../api/partner';
import type { FavoriteArtifact } from '../../api/partner';
import ArtifactCard from '../../components/ArtifactCard';

const { Title, Text } = Typography;

const PartnerFavorites: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<FavoriteArtifact[]>([]);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const response = await partnerAPI.getFavorites();
      setFavorites(response.data || []);
    } catch (error) {
      console.error(error);
      message.error('Не удалось загрузить избранные артефакты');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (favoriteId: number, artifactTitle: string) => {
    try {
      await partnerAPI.removeFavorite(favoriteId);
      message.success(`«${artifactTitle}» удалено из избранного`);
      await fetchFavorites();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось удалить из избранного');
    }
  };

  const handleRequestFullText = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'full_text' });
      message.success('Запрос на полный текст отправлен куратору');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось отправить запрос');
    }
  };

  const handleInternshipRequest = async (artifactId: number) => {
    try {
      await partnerAPI.createRequest({ artifact_id: artifactId, type: 'internship' });
      message.success('Приглашение на стажировку отправлено');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось отправить приглашение');
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
            <Button
              type="primary"
              style={{ background: '#00AEEF' }}
              onClick={() => navigate('/partner/digest')}
            >
              Перейти к дайджесту
            </Button>
          </Empty>
        </Card>
      ) : (
        favorites.map(favorite => (
          <Card key={favorite.id} style={{ marginBottom: 16, position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div style={{ flex: 1 }}>
                <Title level={5}>{favorite.artifact.title}</Title>
                <Text type="secondary">{favorite.artifact.author_name || 'Автор не указан'}</Text>
              </div>
              <Popconfirm
                title="Удалить из избранного?"
                description="Это действие нельзя отменить"
                onConfirm={() => handleRemoveFavorite(favorite.id, favorite.artifact.title)}
                okText="Да"
                cancelText="Нет"
              >
                <Button type="text" danger>
                  ✕ Удалить
                </Button>
              </Popconfirm>
            </div>
            <ArtifactCard
              artifact={favorite.artifact}
              onRequestFullText={handleRequestFullText}
              onInternship={handleInternshipRequest}
              onSaveFavorite={() => message.info('Уже в избранном')}
            />
          </Card>
        ))
      )}
    </div>
  );
};

export default PartnerFavorites;