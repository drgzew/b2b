import {Table, Tag, Button, message} from "antd";
import {useEffect, useState} from "react";
import {apiClient} from "../../api/client";

interface ArtifactRequest {
    id:number;
    artifactTitle:string;
    requester:string;
    requesterRole:string;
    type:string;
    status:string;
    createdAt:string;
}

export default function Requests(){

    const [requests,setRequests]=useState<ArtifactRequest[]>([]);
    const [loading,setLoading]=useState(false);

    useEffect(()=>{
        loadRequests();
    },[]);

    async function loadRequests(){

        try{

            setLoading(true);

            const response =
                await apiClient.get(
                    "/curator/requests"
                );

            setRequests(
                response.data
            );

        }catch{

            message.error(
                "Не удалось загрузить запросы"
            );

        }finally{

            setLoading(false);

        }

    }


    async function updateStatus(
        id:number,
        status:string
    ){

        try{

            await apiClient.patch(
                `/curator/requests/${id}`,
                {
                    status
                }
            );

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


            if(status==="in_progress"){

                message.success(
                    "Запрос взят в работу"
                );

            }


            if(status==="done"){

                message.success(
                    "Запрос выполнен"
                );

            }


        }catch{

            message.error(
                "Ошибка обновления запроса"
            );

        }

    }


    const columns=[

        {
            title:"Партнёр",
            dataIndex:"requester"
        },


        {
            title:"Артефакт",
            dataIndex:"artifactTitle"
        },


        {
            title:"Тип запроса",
            dataIndex:"type"
        },


        {
            title:"Статус",

            dataIndex:"status",

            render:(status:string)=>{

                const config:any={

                    pending:{
                        text:"Новый",
                        color:"blue"
                    },

                    in_progress:{
                        text:"В работе",
                        color:"orange"
                    },

                    done:{
                        text:"Готово",
                        color:"green"
                    }

                };


                return(

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
            title:"Действия",

            render:(
                _:unknown,
                record:ArtifactRequest
            )=>(

                <>

                    {
                        record.status==="pending" && (

                            <Button
                                type="primary"
                                onClick={()=>updateStatus(
                                    record.id,
                                    "in_progress"
                                )}
                            >
                                Взять в работу
                            </Button>

                        )
                    }


                    {
                        record.status==="in_progress" && (

                            <Button
                                onClick={()=>updateStatus(
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


    return(

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
                    pageSize:10
                }}

            />

        </div>

    );

}