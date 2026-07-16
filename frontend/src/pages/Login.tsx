import { Form, Input, Button, Layout, message } from "antd";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { login } from "../api/auth";

const { Content } = Layout;

export default function Login() {
    const navigate = useNavigate();

    async function onFinish(values: any) {
        try {
            const data = await login(values.email, values.password);

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", data.role);

            // Редирект в зависимости от роли
            if (data.role === "curator") {
                navigate("/curator/queue");
                return;
            }
            if (data.role === "partner") {
                navigate("/partner/dashboard");
                return;
            }
            if (data.role === "author") {
                navigate("/author/dashboard");
                return;
            }
            if (data.role === "admin") {
                navigate("/admin");
                return;
            }
            // Если роль неизвестна
            message.error("Неизвестная роль пользователя");
            navigate("/login");
        } catch (error) {
            message.error("Неверный email или пароль");
        }
    }

    return (
        <Layout>
            <Header />
            <Content className="page-container">
                <div className="login-wrapper">
                    <div className="login-card">
                        <h2>Вход в систему</h2>
                        <Form layout="vertical" onFinish={onFinish}>
                            <Form.Item
                                label="Электронная почта"
                                name="email"
                                rules={[{ required: true, message: "Введите email" }]}
                            >
                                <Input />
                            </Form.Item>
                            <Form.Item
                                label="Пароль"
                                name="password"
                                rules={[{ required: true, message: "Введите пароль" }]}
                            >
                                <Input.Password />
                            </Form.Item>
                            <Button htmlType="submit" type="primary" block>
                                Войти
                            </Button>
                        </Form>
                    </div>
                </div>
            </Content>
        </Layout>
    );
}