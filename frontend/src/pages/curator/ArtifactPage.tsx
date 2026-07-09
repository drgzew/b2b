import {useEffect,useState} from "react";
import {Card,Typography,Select,Button,Space,Tag,message,Modal} from "antd";
import {useParams,useNavigate} from "react-router-dom";
import type {Artifact,Tag as TagType} from "../../api/types";
import * as curatorApi from "../../api/curator";
import * as tagsApi from "../../api/tags";

const {Title,Text}=Typography;

export default function ArtifactPage(){

    const {id}=useParams();
    const navigate=useNavigate();

    const [artifact,setArtifact]=useState<Artifact>();
    const [allTags,setAllTags]=useState<TagType[]>([]);
    const [selectedTags,setSelectedTags]=useState<number[]>([]);
    const [loading,setLoading]=useState(true);


    useEffect(()=>{

        loadData();

    },[id]);


    async function loadData(){

        if(!id){
            return;
        }

        try{

            setLoading(true);

            const [
                artifactData,
                tagsData
            ]=await Promise.all([

                curatorApi.getArtifact(
                    Number(id)
                ),

                tagsApi.getAll()

            ]);


            setArtifact(
                artifactData
            );

            setAllTags(
                tagsData
            );


            setSelectedTags(
                artifactData.tags.map(
                    tag=>tag.id
                )
            );


        }catch(error){

            message.error(
                "Ошибка загрузки артефакта"
            );

        }finally{

            setLoading(false);

        }

    }



    async function saveTags(){

        if(!artifact){
            return;
        }


        try{

            const updatedArtifact =
                await curatorApi.updateArtifactTags(
                    artifact.id,
                    selectedTags
                );


            setArtifact(
                updatedArtifact
            );


            message.success(
                "Теги сохранены"
            );


        }catch(error){

            message.error(
                "Ошибка сохранения тегов"
            );

        }

    }



    async function approve(){

        if(!artifact){
            return;
        }


        try{

            await curatorApi.approveArtifact(
                artifact.id
            );


            message.success(
                "Работа одобрена"
            );


            navigate(
                "/curator/queue"
            );


        }catch(error){

            message.error(
                "Ошибка одобрения"
            );

        }

    }



    function reject(){

        if(!artifact){
            return;
        }


        Modal.confirm({

            title:"Отклонить работу?",

            content:
                "Работа будет отправлена в статус rejected.",


            okText:"Отклонить",

            cancelText:"Отмена",


            okButtonProps:{
                danger:true
            },


            async onOk(){


                try{

                    await curatorApi.rejectArtifact(
                        artifact.id
                    );


                    message.success(
                        "Работа отклонена"
                    );


                    navigate(
                        "/curator/queue"
                    );


                }catch(error){

                    message.error(
                        "Ошибка отклонения"
                    );

                }

            }

        });

    }



    if(!loading && !artifact){

        return(

            <Title level={3}>
                Артефакт не найден
            </Title>

        );

    }



    return(

        <Card

            loading={loading}

            style={{

                maxWidth:900,

                margin:"30px auto"

            }}

        >

            {
                artifact && (

                    <Space

                        direction="vertical"

                        size="large"

                        style={{

                            width:"100%"

                        }}

                    >

                        <Title level={2}>

                            {artifact.title}

                        </Title>



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
                                {
                                    artifact.annotation
                                }
                            </p>

                        </div>




                        <div>

                            <Text strong>
                                Статус:
                            </Text>


                            <p>

                                {
                                    artifact.curator_status
                                }

                            </p>

                        </div>




                        <div>

                            <Text strong>
                                Текущие теги:
                            </Text>


                            <div
                                style={{
                                    marginTop:10
                                }}
                            >

                                {
                                    artifact.tags.map(
                                        tag=>(

                                            <Tag
                                                key={
                                                    tag.id
                                                }
                                            >

                                                {
                                                    tag.name
                                                }

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

                                showSearch

                                optionFilterProp="label"


                                style={{

                                    width:"100%",

                                    marginTop:10

                                }}


                                placeholder="Выберите теги"


                                value={
                                    selectedTags
                                }


                                onChange={
                                    setSelectedTags
                                }


                                options={

                                    allTags.map(
                                        tag=>({

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

                                    marginTop:10

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

                )
            }


        </Card>

    );

}