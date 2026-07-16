import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, message, Avatar, Tag } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { authorsAPI } from '../../api/authors';
import type { Author } from '../../api/types';

const { Title, Text } = Typography;

const AuthorProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [author, setAuthor] = useState<Author | null>(null);

  useEffect(() => {
    if (id) fetchAuthor(parseInt(id));
  }, [id]);

  const fetchAuthor = async (authorId: number) => {
    setLoading(true);
    try {
      const res = await authorsAPI.getAuthor(authorId);
      setAuthor(res.data);
    } catch (error) {
      message.error('Не удалось загрузить профиль автора');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;
  if (!author) return <div>Автор не найден</div>;

  const statusMap: Record<string, string> = {
    searching: 'Ищет работу',
    not_searching: 'Не ищет работу',
    employed: 'Работает',
  };

  return (
    <div className="page-container">
      <Card>
        <div style={{ display: 'flex', gap: 24 }}>
          <Avatar size={120} src={author.photo_url || undefined}>{author.full_name.charAt(0)}</Avatar>
          <div>
            <Title level={3}>{author.full_name}</Title>
            <Text>Направление: {author.program || 'не указано'}</Text>
            <br />
            <Text>Статус: <Tag color={author.job_status === 'searching' ? 'blue' : 'green'}>
              {statusMap[author.job_status] || author.job_status}
            </Tag></Text>
          </div>
        </div>
      </Card>
      <div style={{ marginTop: 16 }}><Button onClick={() => navigate(-1)}>Назад</Button></div>
    </div>
  );
};

export default AuthorProfile;