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
    decideRequest,
    takeRequest,
    updateRequestStatus
} from "../api/curatorRequests";

import type {
    PartnerRequest
} from "../api/types";


const { Title, Text } = Typography;


interface Props {
    request: PartnerRequest;
    reload: () => void;
}


// Статусы запроса на бэкенде: sent | in_progress | approved | rejected | done
const getStatusLabel = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
        sent: {
            label: "Отправлено",
            color: "blue"
        },
        in_progress: {
            label: "В работе",
            color: "orange"
        },
        approved: {
            label: "Доступ выдан",
            color: "green"
        },
        rejected: {
            label: "Отклонено",
            color: "red"
        },
        done: {
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


    // Одобрение/отклонение запроса на полный текст: одобрение выдаёт
    // партнёру доступ к документу (grant_read_access на бэкенде).
    async function handleDecision(approve: boolean) {
        setLoading(true);

        try {
            await decideRequest(
                request.id,
                approve
            );

            message.success(
                approve
                    ? "Доступ к полному тексту выдан партнёру"
                    : "Запрос отклонён"
            );

            reload();

        } catch (error: any) {
            message.error(
                error.response?.data?.detail ||
                "Не удалось обработать запрос"
            );

        } finally {
            setLoading(false);
        }
    }


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


    async function handleDone() {
        setLoading(true);

        try {
            await updateRequestStatus(
                request.id,
                "done"
            );

            message.success(
                "Запрос завершён"
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


    const isFullText = request.type === "full_text";


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
                        // Запрос полного текста решается сразу: одобрить
                        // (выдать доступ) или отклонить.
                        isFullText &&
                        request.status === "sent" &&

                        <>
                            <Button
                                type="primary"
                                onClick={() =>
                                    handleDecision(true)
                                }
                                loading={loading}
                            >
                                Выдать доступ
                            </Button>


                            <Button
                                danger
                                onClick={() =>
                                    handleDecision(false)
                                }
                                loading={loading}
                            >
                                Отклонить
                            </Button>
                        </>

                    }


                    {
                        // Стажировки/НИОКР проходят через рабочий процесс:
                        // взять в работу -> завершить.
                        !isFullText &&
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

                        <Button
                            type="primary"
                            onClick={handleDone}
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
