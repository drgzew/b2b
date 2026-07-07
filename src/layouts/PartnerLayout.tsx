import {Layout} from "antd";

import Header from "../components/Header";

interface CuratorLayoutProps {
    children:React.ReactNode;
}

const {
    Content
} = Layout;

export default function CuratorLayout({
    children
}:CuratorLayoutProps) {

    return (
        <Layout>
            <Header
                title="Кабинет партнёра"

                menuItems={[
                    {
                        label:"Дашборд",
                        path:"/"
                    },
                    {
                        label:"Подписки",
                        path:"/"
                    }
                ]}
            />

            <Content>
                {children}
            </Content>

        </Layout>
    );
}