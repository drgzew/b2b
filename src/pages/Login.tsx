import { Form, Input, Button, Select, Layout } from "antd";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";

const { Content } = Layout;

export default function Login() {
    const navigate = useNavigate();

    function onFinish(values: any) {
        localStorage.setItem(
            "role",
            values.role
        );

        if (values.role === "partner") {
            navigate("/partner/dashboard");
        }

        if (values.role === "curator") {
            navigate("/curator/queue");
        }
    }

    return (
        <Layout>
            <Header />
            <Content className="page-container">
                <div className="login-wrapper">
                    <div className="login-card">
                        <h2>
                            Вход в систему
                        </h2>

                        <Form
                            layout="vertical"
                            onFinish={onFinish}
                        >
                            <Form.Item
                                label="Электронная почта"
                                name="email"
                                rules={[
                                    {
                                        required: true,
                                        message: "Введите email"
                                    }
                                ]}
                            >
                                <Input
                                    placeholder="partner@company.ru" />
                            </Form.Item>

                            <Form.Item
                                label="Пароль"
                                name="password"
                                rules={[
                                    {
                                        required: true,
                                        message: "Введите пароль"
                                    }
                                ]}
                            >
                                <Input.Password
                                    placeholder="••••••••" />
                            </Form.Item>

                            <Form.Item
                                label="Роль"
                                name="role"
                                initialValue="curator"
                            >
                                <Select
                                    options={[
                                        {
                                            label: "Участник",
                                            value: "participant"
                                        },
                                        {
                                            label: "Партнёр",
                                            value: "partner"
                                        },
                                        {
                                            label: "Куратор",
                                            value: "curator"
                                        },
                                        {
                                            label: "Администратор",
                                            value: "admin"
                                        }
                                    ]} />
                            </Form.Item>

                            <Button
                                htmlType="submit"
                                className="btn-primary"
                            >
                                Войти
                            </Button>
                        </Form>

                    </div>
                </div>
        </Content>
    </Layout >
    );
}