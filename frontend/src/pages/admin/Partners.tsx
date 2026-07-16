import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Modal, Form, Input, Typography, message } from 'antd';
import { adminAPI } from '../../api/admin';
import type { AdminPartner } from '../../api/admin';

const Partners: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [partners, setPartners] = useState<AdminPartner[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  async function load() {
    setLoading(true);
    try {
      const res = await adminAPI.getPartners();
      setPartners(res.data);
    } catch {
      message.error('Не удалось загрузить партнёров');
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
      await adminAPI.createPartner(values);
      message.success('Партнёр создан');
      setModalOpen(false);
      form.resetFields();
      await load();
    } catch (error: any) {
      if (error?.errorFields) return;
      message.error(error.response?.data?.detail || 'Не удалось создать партнёра');
    } finally {
      setCreating(false);
    }
  }

  return (
    <Card
      title="Партнёры"
      extra={
        <Button type="primary" onClick={() => setModalOpen(true)}>
          + Добавить партнёра
        </Button>
      }
    >
      <Table
        rowKey="id"
        loading={loading}
        dataSource={partners}
        pagination={false}
        columns={[
          { title: 'Название', dataIndex: 'name' },
          { title: 'Контактный email', dataIndex: 'contact_email' },
        ]}
      />

      <Modal
        title="Новый партнёр"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        confirmLoading={creating}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Название компании" rules={[{ required: true, message: 'Укажите название' }]}>
            <Input placeholder="Например, Газпромнефть" />
          </Form.Item>
          <Form.Item
            name="contact_email"
            label="Контактный email"
            rules={[{ required: true, message: 'Укажите email' }, { type: 'email', message: 'Некорректный email' }]}
          >
            <Input />
          </Form.Item>
        </Form>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          После создания партнёра заведите для него учётку на странице «Пользователи»
          (роль «Партнёр»), чтобы он мог войти в систему.
        </Typography.Text>
      </Modal>
    </Card>
  );
};

export default Partners;
