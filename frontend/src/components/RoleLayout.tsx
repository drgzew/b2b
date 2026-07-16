import React from 'react';
import { Layout } from 'antd';
import Header from './Header';
import PartnerLayout from '../layouts/PartnerLayout';
import CuratorLayout from '../layouts/CuratorLayout';
import AdminLayout from '../layouts/AdminLayout';

const { Content } = Layout;

interface RoleLayoutProps {
  children: React.ReactNode;
}

const RoleLayout: React.FC<RoleLayoutProps> = ({ children }) => {
  const role = localStorage.getItem('role');

  if (role === 'partner') {
    return <PartnerLayout>{children}</PartnerLayout>;
  }

  if (role === 'curator') {
    return <CuratorLayout>{children}</CuratorLayout>;
  }

  if (role === 'admin') {
    return <AdminLayout>{children}</AdminLayout>;
  }

  // Автор попадает сюда только на общих страницах (/profile/*): его кабинет
  // (/author/*) обёрнут в AuthorLayout на уровне роутера. Показываем то же
  // меню, чтобы навигация не пропадала.
  if (role === 'author') {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          title="Кабинет автора"
          menuItems={[
            { label: 'Мои работы', path: '/author/dashboard' },
            { label: 'Запросы', path: '/author/requests' },
            { label: '💼 Приглашения', path: '/author/internships' },
          ]}
        />
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8 }}>
          {children}
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header title="Кабинет" menuItems={[]} />
      <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8 }}>
        {children}
      </Content>
    </Layout>
  );
};

export default RoleLayout;