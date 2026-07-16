import { Layout } from "antd";
import Header from "../components/Header";

interface AdminLayoutProps {
    children: React.ReactNode;
}

const { Content } = Layout;

export default function AdminLayout({
    children
}: AdminLayoutProps) {

    return (
        <Layout>
            <Header
                title="Кабинет администратора"
                menuItems={[
                    {
                        label: "Дашборд",
                        path: "/admin"
                    },
                    {
                        label: "Модерация",
                        path: "/curator/queue"
                    },
                    {
                        label: "Запросы",
                        path: "/curator/requests"
                    },
                    {
                        label: "Пользователи",
                        path: "/admin/users"
                    },
                    {
                        label: "Партнёры",
                        path: "/admin/partners"
                    },
                    {
                        label: "Импорт данных",
                        path: "/admin/import"
                    }
                ]}
            />
            <Content className="page-container">
                {children}
            </Content>
        </Layout>
    );
}
