import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Modal, Form, Input, Select, message } from 'antd';
import { adminAPI } from '../../api/admin';
import type { AdminUser, AdminPartner, AdminAuthor } from '../../api/admin';

const roleLabel: Record<string, { text: string; color: string }> = {
  admin: { text: 'Администратор', color: 'purple' },
  curator: { text: 'Куратор', color: 'blue' },
  partner: { text: 'Партнёр', color: 'green' },
  author: { text: 'Автор', color: 'orange' },
};

const Users: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [partners, setPartners] = useState<AdminPartner[]>([]);
  const [authors, setAuthors] = useState<AdminAuthor[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();
  const selectedRole = Form.useWatch('role', form);

  async function load() {
    setLoading(true);
    try {
      const [usersRes, partnersRes, authorsRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getPartners(),
        adminAPI.getAuthors(),
      ]);
      setUsers(usersRes.data);
      setPartners(partnersRes.data);
      setAuthors(authorsRes.data);
    } catch {
      message.error('Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate() {
    try {
      const values = await form.validateFields();
      setCreating(true);
      await adminAPI.createUser(values);
      message.success('Пользователь создан');
      setModalOpen(false);
      form.resetFields();
      await load();
    } catch (error: any) {
      if (error?.errorFields) return; // ошибка валидации формы — antd сам подсветит поля
      message.error(error.response?.data?.detail || 'Не удалось создать пользователя');
    } finally {
      setCreating(false);
    }
  }

  return (
    <Card
      title="Пользователи"
      extra={
        <Button type="primary" onClick={() => setModalOpen(true)}>
          + Добавить пользователя
        </Button>
      }
    >
      <Table
        rowKey="id"
        loading={loading}
        dataSource={users}
        pagination={false}
        columns={[
          { title: 'Email', dataIndex: 'email' },
          {
            title: 'Роль',
            dataIndex: 'role',
            render: (role: string) => {
              const r = roleLabel[role] ?? { text: role, color: 'default' };
              return <Tag color={r.color}>{r.text}</Tag>;
            },
          },
          {
            title: 'Учётная запись',
            key: 'linked_account',
            render: (_: unknown, record: AdminUser) => {
              if (record.role === 'partner') {
                if (!record.partner_id) return '—';
                return partners.find(p => p.id === record.partner_id)?.name ?? `#${record.partner_id}`;
              }
              if (record.role === 'author') {
                if (!record.author_id) return '—';
                return authors.find(a => a.id === record.author_id)?.full_name ?? `#${record.author_id}`;
              }
              return '—';
            },
          },
        ]}
      />

      <Modal
        title="Новый пользователь"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        confirmLoading={creating}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="email"
            label="Email"
            rules={[{ required: true, message: 'Укажите email' }, { type: 'email', message: 'Некорректный email' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="Пароль"
            rules={[{ required: true, message: 'Укажите пароль' }, { min: 6, message: 'Минимум 6 символов' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="Роль" rules={[{ required: true, message: 'Выберите роль' }]}>
            <Select
              options={[
                { value: 'partner', label: 'Партнёр' },
                { value: 'curator', label: 'Куратор' },
                { value: 'admin', label: 'Администратор' },
                { value: 'author', label: 'Автор' },
              ]}
            />
          </Form.Item>
          {selectedRole === 'partner' && (
            <Form.Item
              name="partner_id"
              label="Партнёр"
              rules={[{ required: true, message: 'Обязательно для роли «Партнёр»' }]}
              extra="Учётка привязывается к компании — сначала создайте партнёра на странице «Партнёры», если его ещё нет в списке."
            >
              <Select
                options={partners.map(p => ({ value: p.id, label: p.name }))}
                placeholder="Выберите партнёра"
              />
            </Form.Item>
          )}
          {selectedRole === 'author' && (
            <Form.Item
              name="author_id"
              label="ID автора"
              rules={[{ required: true, message: 'Обязательно для роли «Автор»' }]}
              extra="Профиль автора создаётся при импорте ВКР/статей парсером, отдельной формы для ручного создания пока нет — укажите id уже существующего профиля."
            >
              <Input type="number" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  );
};

export default Users;
