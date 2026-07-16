import React from "react";
import {
    Card,
    Button,
    Tag,
    Typography,
    Space,
    message
} from "antd";

import {
    takeRequest,
    updateRequestStatus
} from "../api/curatorRequests";

import type {
    PartnerRequest,
    RequestStatus
} from "../api/types";


const { Title, Text } = Typography;


interface Props {
    request: PartnerRequest;
    reload: () => void;
}


const getStatusLabel = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
        sent: {
            label: "Отправлено",
            color: "blue"
        },
        accepted: {
            label: "Принято",
            color: "green"
        },
        in_progress: {
            label: "В процессе",
            color: "orange"
        },
        rejected: {
            label: "Отклонено",
            color: "red"
        },
        completed: {
            label: "Завершено",
            color: "purple"
        }
    };

    return (
        statusMap[status] || {
            label: status,
            color: "default"
        }
    );
};


const getTypeLabel = (type: string) => {
    const types: Record<string, string> = {
        full_text: "Полный текст",
        internship: "Стажировка",
        rnd: "НИОКР"
    };

    return types[type] || type;
};


export default function RequestCard({
    request,
    reload
}: Props) {

    const [loading, setLoading] = React.useState(false);

    const statusInfo = getStatusLabel(request.status);


    async function handleTake() {
        setLoading(true);

        try {
            await takeRequest(request.id);

            message.success(
                "Запрос взят в работу"
            );

            reload();

        } catch (error: any) {
            message.error(
                error.response?.data?.detail ||
                "Не удалось взять запрос"
            );

        } finally {
            setLoading(false);
        }
    }


    async function handleStatus(status: RequestStatus) {
        setLoading(true);

        try {
            await updateRequestStatus(
                request.id,
                status
            );

            message.success(
                `Статус изменён на "${getStatusLabel(status).label}"`
            );

            reload();

        } catch (error: any) {
            message.error(
                error.response?.data?.detail ||
                "Не удалось изменить статус"
            );

        } finally {
            setLoading(false);
        }
    }


    return (
        <Card
            style={{
                marginBottom: 16
            }}
        >

            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start"
                }}
            >

                <div style={{ flex: 1 }}>

                    <Title level={5}>
                        {request.artifact.title}
                    </Title>


                    <div
                        style={{
                            marginBottom: 12
                        }}
                    >

                        <Text type="secondary">
                            Компания:{" "}
                        </Text>

                        <Text strong>
                            {request.partner.name}
                        </Text>


                        <br />


                        <Text type="secondary">
                            Автор:{" "}
                            {
                                request.artifact.author_name ||
                                "Не указан"
                            }
                        </Text>

                    </div>


                    <Space>

                        <Tag color="cyan">
                            {
                                getTypeLabel(
                                    request.type
                                )
                            }
                        </Tag>


                        <Tag color={statusInfo.color}>
                            {statusInfo.label}
                        </Tag>

                    </Space>

                </div>


                <Space
                    wrap
                    style={{
                        justifyContent: "flex-end"
                    }}
                >

                    {
                        request.status === "sent" &&

                        <Button
                            onClick={handleTake}
                            loading={loading}
                        >
                            Взять в работу
                        </Button>

                    }


                    {
                        request.status === "in_progress" &&

                        <>
                            <Button
                                type="primary"
                                onClick={() =>
                                    handleStatus("accepted")
                                }
                                loading={loading}
                            >
                                Принять
                            </Button>


                            <Button
                                danger
                                onClick={() =>
                                    handleStatus("rejected")
                                }
                                loading={loading}
                            >
                                Отклонить
                            </Button>
                        </>

                    }


                    {
                        request.status === "accepted" &&

                        <Button
                            onClick={() =>
                                handleStatus("completed")
                            }
                            loading={loading}
                        >
                           Завершить
                        </Button>

                    }

                </Space>

            </div>

        </Card>
    );
}