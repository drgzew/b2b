import React, { useState } from 'react';
import { Card, Upload, Button, Checkbox, Alert, Descriptions, Typography, Table, message } from 'antd';
import type { UploadFile } from 'antd/es/upload/interface';
import { adminAPI } from '../../api/admin';
import type { ImportResult } from '../../api/admin';

const { Title, Paragraph } = Typography;
const { Dragger } = Upload;

const Import: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [wipe, setWipe] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  async function handleImport() {
    if (fileList.length === 0) {
      message.warning('Сначала выберите файл normalized.json');
      return;
    }
    const file = fileList[0].originFileObj as File;

    setImporting(true);
    setResult(null);
    try {
      const res = await adminAPI.importArtifacts(file, wipe);
      setResult(res.data);
      if (res.data.imported > 0) {
        message.success(`Импортировано ${res.data.imported} из ${res.data.total}`);
      } else {
        message.warning('Ни один артефакт не был импортирован — см. детали ошибок ниже');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Не удалось выполнить импорт');
    } finally {
      setImporting(false);
    }
  }

  return (
    <Card title="Импорт данных из парсера">
      <Paragraph type="secondary">
        Загрузите <code>normalized.json</code>, полученный после{' '}
        <code>parsing/scripts/normalize.py</code> — тот же файл, что раньше
        заливался только через консоль (<code>python -m parsing.scripts.import</code>).
        Результат идентичен независимо от способа запуска.
      </Paragraph>

      <Dragger
        fileList={fileList}
        beforeUpload={() => false} // не грузим сразу — только по кнопке «Импортировать»
        onChange={({ fileList: fl }) => setFileList(fl.slice(-1))} // держим только последний выбранный файл
        accept=".json"
        maxCount={1}
      >
        <p className="ant-upload-text">📄 Нажмите или перетащите normalized.json сюда</p>
      </Dragger>

      <div style={{ marginTop: 16 }}>
        <Checkbox checked={wipe} onChange={e => setWipe(e.target.checked)}>
          Очистить базу перед импортом (артефакты и теги)
        </Checkbox>
        {wipe && (
          <Alert
            style={{ marginTop: 8 }}
            type="warning"
            showIcon
            message="Необратимо: удалит все существующие артефакты, теги и связанные с ними избранное/запросы/стажировки."
          />
        )}
      </div>

      <Button
        type="primary"
        style={{ marginTop: 16 }}
        loading={importing}
        onClick={handleImport}
        disabled={fileList.length === 0}
      >
        Импортировать
      </Button>

      {result && (
        <Card style={{ marginTop: 24 }} type="inner" title="Результат">
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Всего в файле">{result.total}</Descriptions.Item>
            <Descriptions.Item label="Импортировано">{result.imported}</Descriptions.Item>
            <Descriptions.Item label="Пропущено">{result.skipped}</Descriptions.Item>
            <Descriptions.Item label="Ошибок">{result.errors}</Descriptions.Item>
            <Descriptions.Item label="Тегов создано">{result.tags_created}</Descriptions.Item>
            <Descriptions.Item label="Тегов уже было">{result.tags_existing}</Descriptions.Item>
            <Descriptions.Item label="С аннотацией">{result.with_annotation}</Descriptions.Item>
            <Descriptions.Item label="С тегами">{result.with_tags}</Descriptions.Item>
          </Descriptions>

          {result.error_details.length > 0 && (
            <>
              <Title level={5} style={{ marginTop: 16 }}>
                Детали ошибок (первые {result.error_details.length})
              </Title>
              <Table
                size="small"
                pagination={false}
                dataSource={result.error_details.map((text, i) => ({ key: i, text }))}
                columns={[{ title: 'Ошибка', dataIndex: 'text' }]}
              />
            </>
          )}
        </Card>
      )}
    </Card>
  );
};

export default Import;
