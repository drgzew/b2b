import { Layout } from "antd";
import Header from "../components/Header";
import { useEffect, useState } from "react";
import { getCuratorStats } from "../api/curator";

interface CuratorLayoutProps {children: React.ReactNode;}
const { Content } = Layout;

export default function CuratorLayout({
    children
}: CuratorLayoutProps) {

    const [stats, setStats] = useState({
        draft: 0,
        requests: 0
    });

    useEffect(() => {loadStats()}, []);

    async function loadStats() {
        try {
            const data =
                await getCuratorStats();
            setStats(data);
        } catch {
            console.log("Ошибка загрузки статистики");
        }
    }

    return (
        <Layout>
            <Header
                title="Кабинет куратора"
                menuItems={[
                    {
                        label: "Управление",
                        path: "/curator/queue",
                        badge: stats.draft
                    },
                    // {
                    //     label:"Артефакты",
                    //     path:"/curator/artifacts"
                    // },
                    {
                        label: "Запросы",
                        path: "/curator/requests",
                        badge: stats.requests
                    }
                ]}
            />
            <Content>
                {children}
            </Content>
        </Layout>
    );
}