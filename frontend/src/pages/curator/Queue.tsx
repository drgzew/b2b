import { useEffect, useState } from "react";
import { Table, Input, Select, Card, Row, Col, Tag, Button, Segmented, message } from "antd";
import { useNavigate } from "react-router-dom";
import { getCuratorArtifacts } from "../../api/curator";
import { getAll } from "../../api/tags";
import type { Artifact, Tag as TagType } from "../../api/types";

export default function Queue() {
    const navigate = useNavigate();
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [allTags, setAllTags] = useState<TagType[]>([]);
    const [status, setStatus] = useState<string>("draft");
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");
    const [authorSearch, setAuthorSearch] = useState("");
    const [yearFilter, setYearFilter] = useState<number>();
    const [typeFilter, setTypeFilter] = useState("");
    const [tagFilter, setTagFilter] = useState<number[]>([]);

    useEffect(() => { loadArtifacts(); }, [status]);
    useEffect(() => { loadTags(); }, []);

    async function loadArtifacts() {

        try {
            setLoading(true);
            const data = await getCuratorArtifacts(
                status === "all"
                    ? undefined
                    : status
            );
            setArtifacts(data);

        } catch {
            message.error("Ошибка загрузки работ");

        } finally {
            setLoading(false);
        }
    }

    async function loadTags() {
        try {
            const data = await getAll();
            setAllTags(data);
        } catch {
            message.error(
                "Ошибка загрузки тегов"
            );
        }
    }

    function getYear(date: string) {
        return new Date(date).getFullYear();
    }

    const filteredArtifacts = artifacts.filter(artifact => {
        const matchesTitle = artifact.title.toLowerCase().includes(search.toLowerCase());

        const matchesAuthor = !authorSearch || artifact.author_name?.toLowerCase()
            .includes(authorSearch.toLowerCase());

        const matchesYear = !yearFilter || getYear(artifact.created_at) === yearFilter;

        const matchesType = !typeFilter || artifact.type === typeFilter;

        const matchesTags = tagFilter.length === 0 || artifact.tags.some(tag => tagFilter.includes(tag.id));

        return (
            matchesTitle &&
            matchesAuthor &&
            matchesYear &&
            matchesType &&
            matchesTags
        );
    }
    );

    const columns = [
        {
            title: "Название",
            dataIndex: "title",
            key: "title"
        },
        {
            title: "Тип",
            dataIndex: "type",
            key: "type",
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
            title: "Автор",
            dataIndex: "author_name",
            key: "author_name",
            render: (value: string) => value || "Не указан"
        },
        {
            title: "Год",
            key: "year",
            render: (_: unknown, record: Artifact
            ) => getYear(record.created_at)
        },

        {
            title: "Теги",
            key: "tags",
            render: (_: unknown, record: Artifact
            ) => (
                <>
                    {
                        record.tags.map(
                            tag => (
                                <Tag key={tag.id}>
                                    {tag.name}
                                </Tag>
                            )
                        )
                    }
                </>
            )
        },

        {
            title: "Действия",
            key: "actions",
            render: (_: unknown, record: Artifact
            ) => (
                <Button
                    type="primary"
                    onClick={() => {
                        navigate(`/curator/artifact/${record.id}`);
                    }}
                >
                    Открыть
                </Button>
            )
        }
    ];

    return (
        <div className="page-container">
            <h1 style={{marginBottom: 24}}>
                Управление публикациями
            </h1>

            <Segmented
                value={status}
                onChange={(value) => setStatus(value.toString())}
                options={[
                    {
                        label: "Все",
                        value: "all"
                    },
                    {
                        label: "На проверке",
                        value: "draft"
                    },
                    {
                        label: "Одобренные",
                        value: "approved"
                    },
                    {
                        label: "Отказано",
                        value: "rejected"
                    }
                ]}
                style={{marginBottom: 24}}
            />

            <Row
                gutter={16}
                style={{marginBottom: 24}}
            >
                <Col span={6}>
                    <Card title="Всего" size="small">
                        {artifacts.length}
                    </Card>
                </Col>

                <Col span={6}>
                    <Card title="Показано" size="small">
                        {filteredArtifacts.length}
                    </Card>
                </Col>
            </Row>

            <Row
                gutter={16}
                style={{marginBottom: 24}}
            >
                <Col span={5}>
                    <Input
                        placeholder="Название"
                        onChange={e => setSearch(e.target.value)}
                    />
                </Col>

                <Col span={5}>
                    <Input
                        placeholder="Автор"
                        onChange={e =>setAuthorSearch(e.target.value)
                        }
                    />
                </Col>

                <Col span={4}>
                    <Select
                        allowClear
                        placeholder="Год"
                        style={{width: "100%"}}
                        onChange={setYearFilter}
                        options={[
                            ...new Set(
                                artifacts.map(
                                    item => getYear(item.created_at)
                                )
                            )
                        ].map(
                            year => ({
                                label: year,
                                value: year
                            })
                        )}
                    />
                </Col>

                <Col span={5}>
                    <Select
                        allowClear
                        placeholder="Тип"
                        style={{width: "100%"}}
                        onChange={value =>setTypeFilter(value || "")}
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

                <Col span={5}>
                    <Select
                        mode="multiple"
                        allowClear
                        showSearch
                        placeholder="Теги"
                        style={{width: "100%"}}
                        value={tagFilter}
                        onChange={setTagFilter}
                        optionFilterProp="label"
                        options={
                            allTags.map(
                                tag => ({
                                    label:
                                        tag.name,
                                    value:
                                        tag.id
                                })
                            )
                        }
                    />
                </Col>
            </Row>

            <Table
                rowKey="id"
                loading={loading}
                columns={columns}
                dataSource={filteredArtifacts}
                pagination={{pageSize: 10}}
            />
        </div>
    );
}