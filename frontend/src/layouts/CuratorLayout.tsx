import { Layout } from "antd";
import Header from "../components/Header";
import { useEffect, useState } from "react";
import { getCuratorStats } from "../api/curator";

interface CuratorLayoutProps { children: React.ReactNode; }
const { Content } = Layout;

export default function CuratorLayout({
    children
}: CuratorLayoutProps) {

    const [stats, setStats] = useState({
        draft: 0,
        requests: 0
    });

    async function loadStats() {

        try {
            const data =
                await getCuratorStats();

            setStats(data);
        } catch {
            console.log(
                "Ошибка загрузки статистики"
            );
        }
    }

    useEffect(() => {
        loadStats();

        // обновление после действий куратора
        window.addEventListener(
            "curatorStatsUpdate",
            loadStats
        );

        // автообновление новых запросов
        const interval = setInterval(
            () => {
                loadStats();
            },
            10000
        );

        return () => {

            window.removeEventListener(
                "curatorStatsUpdate",
                loadStats
            );

            clearInterval(
                interval
            );
        };
    }, []);

    return (
        <Layout>
            <Header
                title="Кабинет куратора"
                menuItems={[
                    {
                        label: `Управление ${stats.draft}`,
                        path: "/curator/queue"
                    },
                    {
                        label: `Запросы ${stats.requests}`,
                        path: "/curator/requests"
                    }
                ]}
            />
            <Content>
                {children}
            </Content>
        </Layout>
    );
}