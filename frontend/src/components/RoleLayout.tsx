import React from 'react';
import { Layout } from 'antd';
import Header from './Header';
import PartnerLayout from '../layouts/PartnerLayout';

const { Content } = Layout;

interface RoleLayoutProps {
  children: React.ReactNode;
}

const RoleLayout: React.FC<RoleLayoutProps> = ({ children }) => {
  const role = localStorage.getItem('role');

  if (role === 'partner') {
    return <PartnerLayout>{children}</PartnerLayout>;
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