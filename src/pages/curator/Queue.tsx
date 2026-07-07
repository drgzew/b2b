import { useState } from "react";
import { Table, Input, Select, Card, Row, Col, Tag, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { artifacts } from "../../mocks/artifacts";
import type { Artifact } from "../../api/types";

export default function Queue() {

    const navigate = useNavigate();

    const [search, setSearch] = useState("");
    const [typeFilter, setTypeFilter] = useState("");
    const [statusFilter, setStatusFilter] = useState("");

    const filteredArtifacts =
        artifacts.filter((artifact) => {

            const matchesSearch =
                artifact.title
                    .toLowerCase()
                    .includes(
                        search.toLowerCase()
                    );

            const matchesType =
                !typeFilter ||
                artifact.type === typeFilter;

            const matchesStatus =
                !statusFilter ||
                artifact.status === statusFilter;

            return (
                matchesSearch &&
                matchesType &&
                matchesStatus
            );
        });

    function getYear(
        date: string
    ) {
        return new Date(date)
            .getFullYear();
    }

    const columns = [
        {
            title: "Название",
            dataIndex: "title"
        },

        {
            title: "Тип",
            dataIndex: "type",
            render: (type: string) => (

                <Tag>
                    {
                        {
                            vkr: "ВКР",
                            article: "Статья",
                            talk: "Доклад",
                            event: "Мероприятие"
                        }[type] || type
                    }
                </Tag>

            )
        },

        {
            title: "Год",
            render: (
                _: unknown,
                record: Artifact
            ) => (
                getYear(
                    record.created_at
                )
            )
        },

        {
            title: "Статус",
            dataIndex: "status",
            render: (
                status: Artifact["status"]
            ) => {
                const config = {
                    moderation: {
                        color: "blue",
                        text: "На проверке"
                    },
                    published: {
                        color: "green",
                        text: "Опубликовано"
                    },
                    rejected: {
                        color: "red",
                        text: "Отклонено"
                    }
                };

                return (
                    <Tag
                        color={
                            config[status].color
                        }
                    >
                        {
                            config[status].text
                        }
                    </Tag>
                );
            }
        },

        {
            title: "Действия",
            render: (
                _: unknown,
                record: Artifact
            ) => (
                <Button
                    type="primary"
                    onClick={() =>
                        navigate(
                            `/curator/artifact/${record.id}`
                        )
                    }
                >
                    Открыть
                </Button>
            )
        }
    ];

    return (

        <div
            style={{
                padding: 24
            }}
        >
            <h1>
                Управление публикациями
            </h1>

            <Row
                gutter={16}
                style={{
                    marginTop: 24,
                    marginBottom: 24
                }}
            >
                <Col span={6}>
                    <Card title="Всего">
                        {
                            artifacts.length
                        }
                    </Card>
                </Col>

                <Col span={6}>
                    <Card title="На проверке">
                        {
                            artifacts.filter(
                                item =>
                                    item.status === "moderation"
                            ).length
                        }
                    </Card>
                </Col>

                <Col span={6}>
                    <Card title="Опубликовано">
                        {
                            artifacts.filter(
                                item =>
                                    item.status === "published"
                            ).length
                        }
                    </Card>
                </Col>

                <Col span={6}>
                    <Card title="Отклонено">
                        {
                            artifacts.filter(
                                item =>
                                    item.status === "rejected"
                            ).length
                        }
                    </Card>
                </Col>

            </Row>

            <Row
                gutter={16}
                style={{
                    marginBottom: 24
                }}
            >
                <Col span={10}>
                    <Input.Search
                        placeholder="Поиск по названию"
                        onChange={(e) =>
                            setSearch(
                                e.target.value
                            )
                        }
                    />
                </Col>

                <Col span={7}>
                    <Select
                        style={{
                            width: "100%"
                        }}
                        placeholder="Тип"
                        allowClear
                        onChange={(value) =>
                            setTypeFilter(
                                value || ""
                            )
                        }
                        options={[
                            {
                                label: "ВКР",
                                value: "vkr"
                            },
                            {
                                label: "Статья",
                                value: "article"
                            },
                            {
                                label: "Доклад",
                                value: "talk"
                            },
                            {
                                label: "Мероприятие",
                                value: "event"
                            }
                        ]}
                    />
                </Col>

                <Col span={7}>
                    <Select
                        style={{
                            width: "100%"
                        }}
                        placeholder="Статус"
                        allowClear
                        onChange={(value) =>
                            setStatusFilter(
                                value || ""
                            )
                        }
                        options={[
                            {
                                label: "На проверке",
                                value: "moderation"
                            },
                            {
                                label: "Опубликовано",
                                value: "published"
                            },
                            {
                                label: "Отклонено",
                                value: "rejected"
                            }
                        ]}
                    />
                </Col>

            </Row>

            <Table
                rowKey="id"
                columns={columns}
                dataSource={filteredArtifacts}
                pagination={{
                    pageSize: 10,
                    showSizeChanger: false,
                    showTotal: (
                        total,
                        range
                    ) =>
                        `${range[0]}-${range[1]} из ${total}`
                }}
            />

        </div>
    );
}