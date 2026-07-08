import React, { useState, useEffect } from 'react';
import { Modal, Checkbox, Button, Input, Tag, message } from 'antd';
import { topics } from '../mocks/topics';

interface SubscriptionManagerProps {
  visible: boolean;
  onClose: () => void;
  onSave: (selectedTopicIds: number[]) => void;
  selectedTopicIds: number[];
}

const SubscriptionManager: React.FC<SubscriptionManagerProps> = ({
  visible,
  onClose,
  onSave,
  selectedTopicIds,
}) => {
  const [tempSelectedIds, setTempSelectedIds] = useState<number[]>(selectedTopicIds);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (visible) {
      setTempSelectedIds(selectedTopicIds);
    }
  }, [visible, selectedTopicIds]);

  const filteredTopics = topics.filter(topic =>
    topic.name.toLowerCase().includes(search.toLowerCase()) ||
    topic.description.toLowerCase().includes(search.toLowerCase()) ||
    topic.tags.some(tag => tag.name.toLowerCase().includes(search.toLowerCase()))
  );

  const handleToggle = (topicId: number) => {
    setTempSelectedIds(prev =>
      prev.includes(topicId) ? prev.filter(id => id !== topicId) : [...prev, topicId]
    );
  };

  const handleSave = () => {
    if (tempSelectedIds.length === 0) {
      message.warning('Выберите хотя бы одну тему для подписки');
      return;
    }
    onSave(tempSelectedIds);
    onClose();
  };

  return (
    <Modal
      title="Управление подписками"
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>Отмена</Button>,
        <Button key="save" type="primary" style={{ background: '#00AEEF' }} onClick={handleSave}>
          Сохранить
        </Button>,
      ]}
      width={600}
    >
      <Input
        placeholder="🔍 Поиск по темам и тегам..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: 16 }}
      />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 400, overflowY: 'auto' }}>
        {filteredTopics.map(topic => {
          const isChecked = tempSelectedIds.includes(topic.id);
          return (
            <div
              key={topic.id}
              style={{
                padding: '12px 16px',
                border: `1px solid ${isChecked ? '#00AEEF' : '#e8ecf0'}`,
                borderRadius: 8,
                background: isChecked ? '#f0f7ff' : 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onClick={() => handleToggle(topic.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong style={{ color: isChecked ? '#00AEEF' : '#1a2a3a' }}>
                    {topic.name}
                  </strong>
                  <div style={{ fontSize: 14, color: '#6b7a8a', marginTop: 4 }}>
                    {topic.description}
                  </div>
                  <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {topic.tags.slice(0, 6).map(tag => (
                      <Tag key={tag.id} color={isChecked ? '#00AEEF' : undefined}>
                        {tag.name}
                      </Tag>
                    ))}
                    {topic.tags.length > 6 && <Tag>+{topic.tags.length - 6}</Tag>}
                  </div>
                </div>
                <Checkbox checked={isChecked} onChange={() => handleToggle(topic.id)} />
              </div>
            </div>
          );
        })}
        {filteredTopics.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7a8a', padding: 20 }}>
            Ничего не найдено
          </div>
        )}
      </div>
    </Modal>
  );
};

export default SubscriptionManager;