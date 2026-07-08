import { Table, Tag, Button, message } from "antd";
import { useState } from "react";
import { requests as mockRequests } from "../../mocks/requests";
import type { ArtifactRequest } from "../../api/types";

export default function Requests() {

    const [
        requests,
        setRequests
    ] = useState<ArtifactRequest[]>(
        mockRequests
    );

    function approve(id: number) {

        setRequests(prev =>
            prev.map(item =>
                item.id === id
                    ? {
                        ...item,
                        status: "approved"
                    }
                    : item
            )
        );

        message.success(
            "Доступ разрешён"
        );
    }

    function reject(id: number) {

        setRequests(prev =>
            prev.map(item =>
                item.id === id
                    ? {
                        ...item,
                        status: "rejected"
                    }
                    : item
            )
        );

        message.error(
            "Доступ отклонён"
        );
    }

    const columns = [
        {
            title: "Артефакт",
            dataIndex:
                "artifactTitle"
        },
        {
            title: "Запросил",
            dataIndex:
                "requester"
        },
        {
            title: "Роль",
            dataIndex:
                "requesterRole"
        },
        {
            title: "Дата",
            dataIndex:
                "createdAt"
        },
        {
            title: "Статус",
            dataIndex:
                "status",
            render:
                (
                    status: string
                ) => {

                    const config: any = {

                        pending: {
                            text: "Ожидает",
                            color: "blue"
                        },

                        approved: {
                            text: "Разрешён",
                            color: "green"
                        },

                        rejected: {
                            text: "Отклонён",
                            color: "red"
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
            render:
                (
                    _: unknown,
                    record: ArtifactRequest
                ) => (
                    record.status === "pending"
                    &&
                    <>
                        <Button
                            type="primary"
                            onClick={() =>
                                approve(
                                    record.id
                                )
                            }
                        >
                            Разрешить
                        </Button>

                        <Button
                            danger
                            style={{
                                marginLeft: 10
                            }}
                            onClick={() =>
                                reject(
                                    record.id
                                )
                            }
                        >
                            Отказать
                        </Button>
                    </>
                )
        }
    ];

    return (
        <div className="page-container">
            <h1 style={{ marginBottom: 24 }}>
                Запросы полного текста
            </h1>

            <Table
                rowKey="id"
                columns={
                    columns
                }
                dataSource={
                    requests
                }
                pagination={{
                    pageSize: 10
                }}
            />
        </div>
    );
}