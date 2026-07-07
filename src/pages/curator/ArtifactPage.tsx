import {Card, Typography, Select, Button, Space, Tag, message} from "antd";
import { useParams } from "react-router-dom";
import { useState } from "react";
import { artifacts } from "../../mocks/artifacts";
import { tags } from "../../mocks/tags";
import type { Artifact as ArtifactType } from "../../api/types";

const {Title, Text} = Typography;

export default function ArtifactPage() {

    const {id} = useParams();

    const initialArtifact =
        artifacts.find(
            item =>
                item.id === Number(id)
        );

    const [
        artifact,
        setArtifact
    ] = useState<ArtifactType | undefined>(
        initialArtifact
    );

    const [
        selectedTags,
        setSelectedTags
    ] = useState<number[]>(
        initialArtifact
            ? initialArtifact.tags.map(
                tag => tag.id
            )
            : []
    );

    if (!artifact) {
        return (
            <Title level={3}>
                Артефакт не найден
            </Title>
        );
    }

    function saveTags() {

        const updatedTags =
            tags.filter(
                tag =>
                    selectedTags.includes(
                        tag.id
                    )
            );

        setArtifact(prev => {
            if (!prev) {
                return prev;
            }
            return {
                ...prev,
                tags: updatedTags
            };
        });

        setSelectedTags(
            updatedTags.map(
                tag => tag.id
            )
        );

        message.success(
            "Теги сохранены"
        );
    }

    function approve() {

        setArtifact(prev => {
            if (!prev) {
                return prev;
            }
            return {
                ...prev,
                status: "published"
            };
        });

        message.success(
            "Работа одобрена"
        );

    }

    function reject() {

        setArtifact(prev => {
            if (!prev) {
                return prev;
            }
            return {
                ...prev,
                status: "rejected"
            };
        });

        message.error(
            "Работа отклонена"
        );
    }

    return (
        <Card className="page-container">
            <Title level={2}>
                {artifact.title}
            </Title>

            <Space
                direction="vertical"
                size="large"
            >

                <div>
                    <Text strong>
                        Автор:
                    </Text>

                    <p>
                        {
                            artifact.author_name
                            ??
                            "Не указан"
                        }
                    </p>
                </div>

                <div>
                    <Text strong>
                        Год:
                    </Text>

                    <p>
                        {
                            new Date(
                                artifact.created_at
                            )
                                .getFullYear()
                        }
                    </p>
                </div>

                <div>
                    <Text strong>
                        Аннотация:
                    </Text>

                    <p>
                        {artifact.annotation}
                    </p>
                </div>

                <div>
                    <Text strong>
                        Текущие теги:
                    </Text>

                    <div
                        style={{
                            marginTop: 10
                        }}
                    >
                        {
                            artifact.tags.map(
                                tag => (
                                    <Tag
                                        key={tag.id}
                                    >
                                        {tag.name}
                                    </Tag>
                                )
                            )
                        }
                    </div>
                </div>

                <div>
                    <Text strong>
                        Изменить теги:
                    </Text>

                    <Select
                        mode="multiple"
                        style={{
                            width: "100%",
                            marginTop: 10
                        }}
                        placeholder="Выберите теги"
                        value={
                            selectedTags
                        }
                        onChange={
                            setSelectedTags
                        }
                        options={
                            tags.map(
                                tag => ({
                                    label:
                                        tag.name,

                                    value:
                                        tag.id
                                })
                            )
                        }
                    />

                    <Button
                        type="primary"
                        style={{
                            marginTop: 10
                        }}
                        onClick={
                            saveTags
                        }
                    >
                        Сохранить теги
                    </Button>
                </div>

                <Space>

                    <Button
                        type="primary"
                        onClick={
                            approve
                        }
                    >
                        Одобрить
                    </Button>

                    <Button
                        danger
                        onClick={
                            reject
                        }
                    >
                        Отклонить
                    </Button>
                </Space>
            </Space>
        </Card>
    );
}