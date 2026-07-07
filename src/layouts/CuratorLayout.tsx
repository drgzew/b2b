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
                title="Кабинет куратора"
                menuItems={[
                    {
                        label:"Управление",
                        path:"/curator/queue"
                    }
                    // ,
                    // {
                    //     label:"Артефакты",
                    //     path:"/curator/artifacts"
                    // }
                ]}
            />

            <Content>
                {children}
            </Content>

        </Layout>
    );
}