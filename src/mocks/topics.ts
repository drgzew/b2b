import type { Tag } from "../api/types";


export interface Topic {
    id: number;
    name: string;
    description: string;
    tags: Tag[];
}


export const topics: Topic[] = [
    {
        id: 1,
        name: "Нефтегазовые технологии",
        description:
            "Исследования в области добычи и моделирования месторождений",
        tags: [
            { id: 1, name: "нефть" },
            { id: 2, name: "газ" },
            { id: 3, name: "моделирование" },
            { id: 4, name: "геология" },
            { id: 5, name: "3D-модель" },
            { id: 21, name: "газовая промышленность" },
            { id: 22, name: "цифровой двойник" },
            { id: 23, name: "сейсмика" },
            { id: 24, name: "бурение" },
        ],
    },


    {
        id: 2,
        name: "Искусственный интеллект",
        description:
            "AI, машинное обучение и интеллектуальные системы",
        tags: [
            { id: 6, name: "AI" },
            { id: 7, name: "машинное обучение" },
            { id: 8, name: "нейросети" },
            { id: 9, name: "NLP" },
            { id: 10, name: "Big Data" },
            { id: 25, name: "computer vision" },
        ],
    },


    {
        id: 3,
        name: "Информационные технологии",
        description:
            "Разработка программных и информационных систем",
        tags: [
            { id: 11, name: "React" },
            { id: 12, name: "Backend" },
            { id: 13, name: "Python" },
            { id: 28, name: "API" },
            { id: 31, name: "информационные системы" },
            { id: 32, name: "кибербезопасность" },
            { id: 33, name: "сети" },
        ],
    },


    {
        id: 4,
        name: "Экология и энергетика",
        description:
            "Экологические исследования и новые источники энергии",
        tags: [
            { id: 14, name: "экология" },
            { id: 15, name: "очистка воды" },
            { id: 16, name: "энергетика" },
            { id: 17, name: "наноматериалы" },
            { id: 29, name: "возобновляемая энергетика" },
        ],
    },
];