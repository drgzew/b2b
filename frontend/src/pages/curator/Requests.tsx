import { Table, Tag, Button, message } from "antd";
import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";
import { updateCuratorStats } from "../../api/events";
import type { ArtifactRequest, RequestStatus } from "../../api/types";

export default function Requests() {
    const [requests, setRequests] = useState<ArtifactRequest[]>([]);
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        loadRequests(true);
        const interval = setInterval(() => {
            loadRequests(false);
        }, 10000);


        return () => {
            clearInterval(interval);
        };


    }, []);

    async function loadRequests(showLoader = true) {
        try {
            if (showLoader) {
                setLoading(true);
            }
            const response = await apiClient.get("/curator/requests");
            setRequests(
                response.data.sort(
                    (a: ArtifactRequest, b: ArtifactRequest) =>
                        new Date(b.created_at).getTime() -
                        new Date(a.created_at).getTime()
                )
            )
        } catch {
            message.error(
                "Не удалось загрузить запросы"
            );
        } finally {
            setLoading(false);
        }
    }

    async function updateStatus(
        id: number,
        status: RequestStatus
    ) {
        try {
            await apiClient.patch(`/curator/requests/${id}`, { status });

            await loadRequests(false);

            updateCuratorStats();

            setRequests(prev =>
                prev.map(item =>
                    item.id === id
                        ? {
                            ...item,
                            status
                        }
                        : item
                )
            );

            if (status === "in_progress") {
                message.success(
                    "Запрос взят в работу"
                );
            }

            if (status === "done") {
                message.success(
                    "Запрос выполнен"
                );
            }

        } catch (error) {
            console.error(error);
            message.error("Ошибка обновления запроса");
        }
    }

    const columns = [
        {
            title: "Партнёр",
            render: (_: any, record: ArtifactRequest) =>
                record.partner.name
        },
        {
            title: "Артефакт",
            render: (_: any, record: ArtifactRequest) =>
                record.artifact.title
        },
        {
            title: "Тип запроса",
            dataIndex: "type"
        },
        {
            title: "Статус",
            dataIndex: "status",
            render: (status: string) => {
                const config: any = {
                    sent: {
                        text: "Новый",
                        color: "blue"
                    },
                    in_progress: {
                        text: "В работе",
                        color: "orange"
                    },
                    done: {
                        text: "Готово",
                        color: "green"
                    }
                };

                return (
                    <Tag
                        color={
                            config[status]?.color
                        }
                    >
                        {
                            config[status]?.text ||
                            status
                        }
                    </Tag>
                );
            }
        },
        {
            title: "Действия",
            render: (
                _: unknown,
                record: ArtifactRequest
            ) => (
                <>
                    {
                        record.status === "sent" && (
                            <Button
                                type="primary"
                                onClick={() => updateStatus(
                                    record.id,
                                    "in_progress"
                                )}
                            >
                                Взять в работу
                            </Button>
                        )
                    }
                    {
                        record.status === "in_progress" && (
                            <Button
                                onClick={() => updateStatus(
                                    record.id,
                                    "done"
                                )}
                            >
                                Готово
                            </Button>
                        )
                    }
                </>
            )
        }
    ];

    return (
        <div className="page-container">
            <h1>
                Запросы полного текста
            </h1>
            <Table
                rowKey="id"
                loading={loading}
                columns={columns}
                dataSource={requests}
                pagination={{
                    pageSize: 10
                }}
            />
        </div>
    );
}