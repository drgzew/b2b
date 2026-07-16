// frontend/src/layouts/AuthorLayout.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Badge } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { authorAPI } from '../api/author';

const { Content } = Layout;

// ✅ Экспортируем тип контекста
export type AuthorLayoutContextType = {
  refreshCounts: () => Promise<void>;
};

const AuthorLayout: React.FC = () => {
  const navigate = useNavigate();
  const [requestCount, setRequestCount] = useState(0);
  const [internshipCount, setInternshipCount] = useState(0);

  const refreshCounts = useCallback(async () => {
    try {
      const [requestsRes, internshipsRes] = await Promise.all([
        authorAPI.getRequests(),
        authorAPI.getInternships(),
      ]);
      setRequestCount(requestsRes.data?.length || 0);
      const sentInternships = (internshipsRes.data || []).filter(
        (inv: any) => inv.status === 'sent'
      );
      setInternshipCount(sentInternships.length);
    } catch (error) {
      console.error('Failed to fetch counts:', error);
    }
  }, []);

  useEffect(() => {
    refreshCounts();
  }, [refreshCounts]);

  const menuItems = [
    { label: 'Мои работы', path: '/author/dashboard' },
    {
      label: (
        <span>
          Запросы
          {requestCount > 0 && (
            <Badge
              count={requestCount}
              style={{ backgroundColor: '#faad14', color: '#fff', marginLeft: 8 }}
            />
          )}
        </span>
      ),
      path: '/author/requests',
    },
    {
      label: (
        <span>
          💼 Приглашения
          {internshipCount > 0 && (
            <Badge
              count={internshipCount}
              style={{ backgroundColor: '#52c41a', color: '#fff', marginLeft: 8 }}
            />
          )}
        </span>
      ),
      path: '/author/internships',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header title="Кабинет автора" menuItems={menuItems} />
      <Content
        style={{
          margin: '24px 16px',
          padding: 24,
          minHeight: 280,
          background: '#fff',
          borderRadius: 8,
        }}
      >
        <Outlet context={{ refreshCounts } satisfies AuthorLayoutContextType} />
      </Content>
    </Layout>
  );
};

export default AuthorLayout;