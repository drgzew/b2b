import { useState } from "react";
import {Table, Input, Select, Card, Row, Col, Tag, Button} from "antd";
import { useNavigate } from "react-router-dom";
import { artifacts } from "../../mocks/artifacts";
import { tags } from "../../mocks/tags";
import type { Artifact } from "../../api/types";

export default function Queue() {

    const navigate = useNavigate();
    const [search, setSearch] = useState("");
    const [authorSearch, setAuthorSearch] = useState("");
    const [yearFilter, setYearFilter] = useState<number | null>(null);
    const [typeFilter, setTypeFilter] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [tagFilter, setTagFilter] = useState<number[]>([]);

    const filteredArtifacts =
        artifacts.filter((artifact) => {

            const matchesTitle =
                artifact.title
                    .toLowerCase()
                    .includes(
                        search.toLowerCase()
                    );

            const matchesAuthor =
                !authorSearch ||
                artifact.author_name
                    ?.toLowerCase()
                    .includes(
                        authorSearch.toLowerCase()
                    );

            const year =
                new Date(
                    artifact.created_at
                )
                .getFullYear();

            const matchesYear =
                !yearFilter ||
                year === yearFilter;

            const matchesType =
                !typeFilter ||
                artifact.type === typeFilter;

            const matchesStatus =
                !statusFilter ||
                artifact.status === statusFilter;

            const matchesTags =
                tagFilter.length === 0 ||
                artifact.tags.some(
                    tag =>
                        tagFilter.includes(
                            tag.id
                        )
                );

            return (
                matchesTitle &&
                matchesAuthor &&
                matchesYear &&
                matchesType &&
                matchesStatus &&
                matchesTags
            );
        });

    function getYear(date:string) {
        return new Date(date)
            .getFullYear();
    }

    const columns = [
        {
            title:"Название",
            dataIndex:"title"
        },
        {
            title:"Тип",
            dataIndex:"type",
            render:(type:string)=>(
                <Tag>
                    {
                        {
                            vkr:"ВКР",
                            article:"Статья",
                            talk:"Доклад",
                            event:"Мероприятие"
                        }[type] || type
                    }
                </Tag>
            )
        },
        {
            title:"Автор",
            dataIndex:"author_name"
        },
        {
            title:"Год",
            render:(
                _:unknown,
                record:Artifact
            )=>
                getYear(
                    record.created_at
                )
        },
        {
            title:"Теги",
            render:(
                _:unknown,
                record:Artifact
            )=>(
                <>
                    {
                        record.tags.map(
                            tag => (
                                <Tag
                                    key={
                                        tag.id
                                    }
                                >
                                    {tag.name}
                                </Tag>
                            )
                        )
                    }
                </>
            )
        },
        {
            title:"Статус",
            dataIndex:"status",
            render:(
                status:Artifact["status"]
            )=>{
                const config = {
                    moderation:{
                        color:"blue",
                        text:"На проверке"
                    },
                    published:{
                        color:"green",
                        text:"Опубликовано"
                    },
                    rejected:{
                        color:"red",
                        text:"Отклонено"
                    }
                };

                const item =
                    config[status];
                return (
                    <Tag
                        color={
                            item?.color
                        }
                    >
                        {
                            item?.text ||
                            status
                        }
                    </Tag>
                );
            }
        },
        {
            title:"Действия",
            render:(
                _:unknown,
                record:Artifact
            )=>(
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
        <div className="page-container">
            <h1>
                Управление публикациями
            </h1>

            <Row
                gutter={16}
                style={{
                    marginTop:24,
                    marginBottom:24
                }}
            >
                <Col span={6}>
                    <Card title="Всего">
                        {artifacts.length}
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
                    marginBottom:24
                }}
            >
                <Col span={6}>
                    <Input
                        placeholder="Поиск по названию"
                        onChange={(e)=>
                            setSearch(
                                e.target.value
                            )
                        }
                    />
                </Col>

                <Col span={6}>
                    <Input
                        placeholder="Поиск по автору"
                        onChange={(e)=>
                            setAuthorSearch(
                                e.target.value
                            )
                        }
                    />
                </Col>

                <Col span={4}>
                    <Select
                        allowClear
                        placeholder="Год"
                        style={{
                            width:"100%"
                        }}
                        onChange={
                            value =>
                                setYearFilter(
                                    value || null
                                )
                        }
                        options={[
                            ...new Set(
                                artifacts.map(
                                    item =>
                                        new Date(
                                            item.created_at
                                        )
                                        .getFullYear()
                                )
                            )
                        ]
                        .map(year=>({
                            label:year,
                            value:year
                        }))}
                    />
                </Col>

                <Col span={4}>
                    <Select
                        allowClear
                        placeholder="Тип"
                        style={{
                            width:"100%"
                        }}
                        onChange={
                            value =>
                                setTypeFilter(
                                    value || ""
                                )
                        }
                        options={[
                            {
                                label:"ВКР",
                                value:"vkr"
                            },
                            {
                                label:"Статья",
                                value:"article"
                            },
                            {
                                label:"Доклад",
                                value:"talk"
                            },
                            {
                                label:"Мероприятие",
                                value:"event"
                            }
                        ]}
                    />
                </Col>

                <Col span={4}>
                    <Select
                        allowClear
                        placeholder="Статус"
                        style={{
                            width:"100%"
                        }}
                        onChange={
                            value =>
                                setStatusFilter(
                                    value || ""
                                )
                        }
                        options={[
                            {
                                label:"На проверке",
                                value:"moderation"
                            },
                            {
                                label:"Опубликовано",
                                value:"published"
                            },
                            {
                                label:"Отклонено",
                                value:"rejected"
                            }
                        ]}
                    />
                </Col>
            </Row>

            <Row
                style={{
                    marginBottom:24
                }}
            >
                <Col span={8}>
                    <Select
                        mode="multiple"
                        showSearch
                        allowClear
                        placeholder="Поиск по тегам"
                        style={{
                            width:"100%"
                        }}
                        value={
                            tagFilter
                        }
                        onChange={
                            setTagFilter
                        }
                        optionFilterProp="label"
                        options={
                            tags.map(
                                tag=>({
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
                columns={columns}
                dataSource={
                    filteredArtifacts
                }
                pagination={{
                    pageSize:10,
                    showSizeChanger:false,
                    showTotal:(
                        total,
                        range
                    )=>
                        `${range[0]}-${range[1]} из ${total}`
                }}
            />
        </div>
    );
}