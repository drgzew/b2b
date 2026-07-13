import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Spin, message } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { teachersAPI } from '../../api/teachers';
import type { Teacher } from '../../api/types';

const { Title, Text } = Typography;

const TeacherProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [teacher, setTeacher] = useState<Teacher | null>(null);

  useEffect(() => {
    if (id) fetchTeacher(parseInt(id));
  }, [id]);

  const fetchTeacher = async (teacherId: number) => {
    setLoading(true);
    try {
      const res = await teachersAPI.getTeacher(teacherId);
      setTeacher(res.data);
    } catch (error) {
      message.error('Не удалось загрузить профиль преподавателя');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />;
  if (!teacher) return <div>Преподаватель не найден</div>;

  return (
    <div className="page-container">
      <Card>
        <Title level={3}>{teacher.full_name}</Title>
        <Text>Email: {teacher.email}</Text>
        <br />
        <Text>Кафедра: {teacher.department}</Text>
        <br />
        <Text>Должность: {teacher.position}</Text>
      </Card>
      <div style={{ marginTop: 16 }}><Button onClick={() => navigate(-1)}>Назад</Button></div>
    </div>
  );
};

export default TeacherProfile;