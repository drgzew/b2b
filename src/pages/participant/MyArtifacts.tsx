import {Button, Card, Table, Tag, Modal, Form, Input, Select, message} from "antd";
import {useState} from "react";
import {artifacts} from "../../mocks/artifacts";
import type {Artifact} from "../../api/types";

export default function MyArtifacts() {

    const [open, setOpen] =
        useState(false);


    const [data, setData] =
        useState<Artifact[]>(
            artifacts
        );


    const [form] =
        Form.useForm();



    function addArtifact() {

        const values =
            form.getFieldsValue();


        const newArtifact: Artifact = {

            id:
                Date.now(),

            title:
                values.title,

            type:
                values.type,

            annotation:
                values.annotation,

            file_path:
                "",

            status:
                "moderation",

            access_level:
                values.access_level,

            author_name:
                "Иванов И.И.",

            created_at:
                new Date()
                    .toISOString(),

            tags:
                []

        };


        setData([
            newArtifact,
            ...data
        ]);


        form.resetFields();

        setOpen(false);


        message.success(
            "Работа отправлена на модерацию"
        );

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
            title:"Статус",

            dataIndex:"status",

            render:(status:string)=>(


                <Tag
                    color={
                        status === "published"
                            ? "green"
                            :
                        status === "moderation"
                            ? "blue"
                            :
                        "red"
                    }
                >

                    {
                        {
                            published:
                                "Опубликовано",

                            moderation:
                                "На проверке",

                            rejected:
                                "Отклонено"

                        }[status]
                    }

                </Tag>

            )

        },


        {
            title:"Доступ",

            dataIndex:"access_level",

            render:(value:string)=>(

                <Tag>

                    {
                        {
                            full:
                                "Полный текст",

                            annotation_only:
                                "Только аннотация",

                            none:
                                "Скрыто"

                        }[value]
                    }

                </Tag>

            )

        }

    ];



    return (

        <div
            style={{
                padding:24
            }}
        >

            <Button
                type="primary"
                onClick={() =>
                    setOpen(true)
                }
            >

                Добавить работу

            </Button>



            <Card
                title="Мои работы"
                style={{
                    marginTop:24
                }}
            >

                <Table

                    rowKey="id"

                    columns={columns}

                    dataSource={data}

                    pagination={{
                        pageSize:10
                    }}

                />

            </Card>





            <Modal

                title="Новая работа"

                open={open}

                onOk={addArtifact}

                onCancel={() =>
                    setOpen(false)
                }

                okText="Отправить"

                cancelText="Отмена"

            >

                <Form
                    form={form}
                    layout="vertical"
                >

                    <Form.Item

                        label="Название"

                        name="title"

                        rules={[
                            {
                                required:true
                            }
                        ]}

                    >

                        <Input/>

                    </Form.Item>



                    <Form.Item

                        label="Тип"

                        name="type"

                    >

                        <Select

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

                    </Form.Item>



                    <Form.Item

                        label="Аннотация"

                        name="annotation"

                    >

                        <Input.TextArea/>

                    </Form.Item>




                    <Form.Item

                        label="Доступ"

                        name="access_level"

                        initialValue="annotation_only"

                    >

                        <Select

                            options={[

                                {
                                    label:
                                    "Полный текст",

                                    value:
                                    "full"
                                },

                                {
                                    label:
                                    "Только аннотация",

                                    value:
                                    "annotation_only"
                                },

                                {
                                    label:
                                    "Не показывать",

                                    value:
                                    "none"
                                }

                            ]}

                        />

                    </Form.Item>


                </Form>


            </Modal>


        </div>
    )
}