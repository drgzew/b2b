import {Card, Typography, Progress, Button, Space} from "antd";
const {Title, Paragraph, Text} = Typography;

interface ArtifactCardProps {
    title:string;
    authors:string[];
    abstract:string;
    relevance:number;
    onRequestFull?: () => void;
    onInternship?: () => void;
}

export default function ArtifactCard({
    title,
    authors,
    abstract,
    relevance,
    onRequestFull,
    onInternship
}:ArtifactCardProps) {

    const clampedRelevance =
        Math.min(
            100,
            Math.max(
                0,
                relevance
            )
        );

    return (
        <Card>
            <Title level={4}>
                {title}
            </Title>

            <Text type="secondary">
                {
                    authors.length > 0
                        ? authors.join(", ")
                        : "Автор не указан"
                }
            </Text>

            <Paragraph>
                {abstract}
            </Paragraph>

            <div>
                <Text strong>
                    Релевантность
                </Text>

                <Progress
                    percent={
                        clampedRelevance
                    }
                    status={
                        clampedRelevance >= 80
                            ? "success"
                            : "active"
                    }
                />
            </div>

            <Space>
                {
                    onRequestFull && (
                        <Button
                            type="primary"
                            onClick={
                                onRequestFull
                            }
                        >
                            Запросить полный текст
                        </Button>
                    )
                }

                {
                    onInternship && (
                        <Button
                            onClick={
                                onInternship
                            }
                        >
                            Пригласить на стажировку
                        </Button>
                    )
                }
            </Space>
        </Card>
    );
}