import {
    useEffect,
    useState
} from "react";

import {
    Card,
    Spin,
    Empty,
    Typography,
    Segmented
} from "antd";

import {
    getCuratorRequests
} from "../../api/curatorRequests";

import type {
    PartnerRequest,
    RequestStatus,
    RequestType
} from "../../api/types";

import RequestCard from "../../components/RequestCard";


const { Title } = Typography;


const CuratorRequests = () => {

    const [requests, setRequests] =
        useState<PartnerRequest[]>([]);

    const [loading, setLoading] =
        useState(true);

    const [status, setStatus] =
        useState<RequestStatus | null>(null);

    const [type, setType] =
        useState<RequestType | null>(null);



    async function load() {

        setLoading(true);

        try {

            const data =
                await getCuratorRequests();


            const sorted =
                [...data].sort(
                    (a, b) =>
                        new Date(b.created_at).getTime()
                        -
                        new Date(a.created_at).getTime()
                );


            setRequests(sorted);


        } finally {

            setLoading(false);

        }

    }



    useEffect(() => {

        load();

    }, []);



    const filteredRequests =
        requests.filter(request => {

            const typeMatch =
                !type ||
                request.type === type;


            const statusMatch =
                !status ||
                request.status === status;


            return (
                typeMatch &&
                statusMatch
            );

        });



    const statusCounts = {

        sent:
            requests.filter(
                r => r.status === "sent"
            ).length,

        in_progress:
            requests.filter(
                r => r.status === "in_progress"
            ).length,

        approved:
            requests.filter(
                r => r.status === "approved"
            ).length,

        rejected:
            requests.filter(
                r => r.status === "rejected"
            ).length,

        done:
            requests.filter(
                r => r.status === "done"
            ).length

    };



    const typeCounts = {

        all:
            requests.length,

        internship:
            requests.filter(
                r => r.type === "internship"
            ).length,

        full_text:
            requests.filter(
                r => r.type === "full_text"
            ).length,

        rnd:
            requests.filter(
                r => r.type === "rnd"
            ).length

    };



    if (loading) {

        return (

            <div
                style={{
                    display: "flex",
                    justifyContent: "center",
                    padding: 50
                }}
            >

                <Spin size="large" />

            </div>

        );

    }



    return (

        <div className="page-container">


            <Title level={4}>
                📩 Управление запросами партнеров
            </Title>



            <Card
                style={{
                    marginBottom: 24,
                    background: "#f0f7ff",
                    borderColor: "#00AEEF"
                }}
            >

                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-around"
                    }}
                >

                    <div style={{ textAlign: "center" }}>

                        <Typography.Text
                            strong
                            style={{
                                fontSize: 18,
                                color: "#00AEEF"
                            }}
                        >
                            {requests.length}
                        </Typography.Text>

                        <br />

                        <Typography.Text type="secondary">
                            Всего запросов
                        </Typography.Text>

                    </div>


                    <div style={{ textAlign: "center" }}>

                        <Typography.Text
                            strong
                            style={{
                                fontSize: 18,
                                color: "#faad14"
                            }}
                        >
                            {statusCounts.in_progress}
                        </Typography.Text>

                        <br />

                        <Typography.Text type="secondary">
                            В работе
                        </Typography.Text>

                    </div>


                    <div style={{ textAlign: "center" }}>

                        <Typography.Text
                            strong
                            style={{
                                fontSize: 18,
                                color: "#52c41a"
                            }}
                        >
                            {statusCounts.done + statusCounts.approved}
                        </Typography.Text>

                        <br />

                        <Typography.Text type="secondary">
                            Завершено
                        </Typography.Text>

                    </div>

                </div>

            </Card>



            <Segmented

                block

                value={
                    type ?? "all"
                }

                onChange={(value) => {

                    setType(
                        value === "all"
                            ? null
                            : value as RequestType
                    );

                }}

                options={[

                    {
                        label:
                            `Все (${typeCounts.all})`,
                        value:
                            "all"
                    },

                    {
                        label:
                            `Стажировка (${typeCounts.internship})`,
                        value:
                            "internship"
                    },

                    {
                        label:
                            `Полный текст (${typeCounts.full_text})`,
                        value:
                            "full_text"
                    },

                    {
                        label:
                            `НИОКР (${typeCounts.rnd})`,
                        value:
                            "rnd"
                    }

                ]}

                style={{
                    marginBottom: 16
                }}

            />



            <Segmented

                block

                value={
                    status ?? "all"
                }

                onChange={(value) => {

                    setStatus(
                        value === "all"
                            ? null
                            : value as RequestStatus
                    );

                }}

                options={[

                    {
                        label:
                            `Все статусы (${requests.length})`,
                        value:
                            "all"
                    },

                    {
                        label:
                            `Новые (${statusCounts.sent})`,
                        value:
                            "sent"
                    },

                    {
                        label:
                            `В работе (${statusCounts.in_progress})`,
                        value:
                            "in_progress"
                    },

                    {
                        label:
                            `Доступ выдан (${statusCounts.approved})`,
                        value:
                            "approved"
                    },

                    {
                        label:
                            `Отклоненные (${statusCounts.rejected})`,
                        value:
                            "rejected"
                    },

                    {
                        label:
                            `Завершенные (${statusCounts.done})`,
                        value:
                            "done"
                    }

                ]}

                style={{
                    marginBottom: 24
                }}

            />



            {
                filteredRequests.length === 0

                    ?

                    <Card>

                        <Empty
                            description="Запросов нет"
                        />

                    </Card>

                    :

                    filteredRequests.map(
                        request => (

                            <RequestCard

                                key={request.id}

                                request={request}

                                reload={load}

                            />

                        )
                    )

            }


        </div>

    );

};


export default CuratorRequests;