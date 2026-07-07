import {
    Layout
} from "antd";

import Header from "../components/Header";

interface ParticipantLayoutProps {
    children: React.ReactNode;
}

const {
    Content
} = Layout;

export default function ParticipantLayout({
    children
}: ParticipantLayoutProps) {

    return (

        <Layout>

            <Header

                title="Кабинет участника"

                menuItems={[
                    {
                        label: "Мои работы",
                        path: "/participant/my-artifacts"
                    },
                    {
                        label: "Запросы",
                        path: "/participant/requests"
                    },
                    {
                        label: "Сообщения",
                        path: "/participant/messages"
                    }
                ]}
            />

            <Content className="page-container">

                {children}

            </Content>

        </Layout>

    );

}