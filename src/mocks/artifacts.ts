import type {
    Artifact
} from "../api/types";


export const artifacts: Artifact[] = [

{
    id:1,
    title:"Моделирование фильтрации нефти в трещиноватых коллекторах",
    type:"vkr",
    annotation:"Разработана математическая модель прогноза продуктивности скважин в сложных геологических условиях.",
    file_path:"/files/artifact-1.pdf",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Иванов И.И., Петров П.П.",
    created_at:"2025-01-15T10:00:00",
    tags:[
        {id:1,name:"нефть"},
        {id:3,name:"моделирование"},
        {id:20,name:"исследование"}
    ]
},

{
    id:2,
    title:"Геологическое строение месторождения Северное",
    type:"article",
    annotation:"Детальный анализ литологии и тектоники месторождения с построением 3D-модели.",
    status:"published",
    access_level:"full",
    author_name:"Сидорова А.В.",
    created_at:"2024-05-10T09:00:00",
    tags:[
        {id:4,name:"геология"},
        {id:5,name:"3D-модель"}
    ]
},

{
    id:3,
    title:"Применение нейросетей для интерпретации ГИС",
    type:"article",
    annotation:"Метод автоматической классификации пород по данным каротажа с использованием сверточных нейронных сетей.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Сидоров С.С., Козлова А.В.",
    created_at:"2024-08-20T12:00:00",
    tags:[
        {id:8,name:"нейросети"},
        {id:7,name:"машинное обучение"}
    ]
},

{
    id:4,
    title:"Мониторинг коррозии трубопроводов с использованием датчиков",
    type:"vkr",
    annotation:"Разработка системы онлайн-мониторинга коррозии на основе ультразвуковых датчиков.",
    status:"moderation",
    access_level:"none",
    author_name:"Захаров В.Г.",
    created_at:"2025-03-12T14:00:00",
    tags:[
        {id:18,name:"коррозия"},
        {id:19,name:"инженерия"}
    ]
},

{
    id:5,
    title:"Применение трансформеров для анализа тональности текстов",
    type:"article",
    annotation:"Сравнение архитектур трансформеров на русскоязычных данных.",
    status:"published",
    access_level:"full",
    author_name:"Иванов Д.С.",
    created_at:"2025-02-01T11:00:00",
    tags:[
        {id:6,name:"AI"},
        {id:9,name:"NLP"}
    ]
},

{
    id:6,
    title:"Архитектура Data Lake для нефтегазовой компании",
    type:"vkr",
    annotation:"Проектирование хранилища данных для объединения геологической и технологической информации.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Григорьева О.В.",
    created_at:"2024-11-10T13:00:00",
    tags:[
        {id:10,name:"Big Data"},
        {id:12,name:"Backend"}
    ]
},

{
    id:7,
    title:"Использование биоплёнок для очистки сточных вод",
    type:"article",
    annotation:"Исследование эффективности микроорганизмов в биореакторах.",
    status:"published",
    access_level:"full",
    author_name:"Максимова Т.В.",
    created_at:"2025-04-05T08:00:00",
    tags:[
        {id:14,name:"экология"},
        {id:15,name:"очистка воды"}
    ]
},

{
    id:8,
    title:"Разработка полимерных нанокомпозитов для защиты от коррозии",
    type:"vkr",
    annotation:"Синтез и тестирование композитных покрытий.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Фёдоров Д.А.",
    created_at:"2025-06-15T15:00:00",
    tags:[
        {id:17,name:"наноматериалы"},
        {id:18,name:"коррозия"}
    ]
},

{
    id:9,
    title:"Оптимизация добычи газа методом машинного обучения",
    type:"article",
    annotation:"Исследование алгоритмов прогнозирования дебита газовых скважин.",
    status:"published",
    access_level:"full",
    author_name:"Орлов Н.П.",
    created_at:"2025-03-01T10:30:00",
    tags:[
        {id:2,name:"газ"},
        {id:7,name:"машинное обучение"}
    ]
},

{
    id:10,
    title:"Цифровой двойник нефтяного месторождения",
    type:"vkr",
    annotation:"Создание цифровой модели объекта для анализа производственных процессов.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Кузнецов А.А.",
    created_at:"2025-05-20T16:00:00",
    tags:[
        {id:22,name:"цифровой двойник"},
        {id:4,name:"геология"}
    ]
},

{
    id:11,
    title:"Анализ сейсмических данных с применением глубокого обучения",
    type:"article",
    annotation:"Использование нейронных сетей для обработки сейсморазведочных данных.",
    status:"published",
    access_level:"full",
    author_name:"Белова Е.С.",
    created_at:"2024-12-12T09:00:00",
    tags:[
        {id:23,name:"сейсмика"},
        {id:8,name:"нейросети"}
    ]
},

{
    id:12,
    title:"Исследование новых методов бурения скважин",
    type:"vkr",
    annotation:"Сравнение эффективности современных технологий бурения.",
    status:"moderation",
    access_level:"none",
    author_name:"Романов И.В.",
    created_at:"2025-02-18T12:00:00",
    tags:[
        {id:24,name:"бурение"},
        {id:1,name:"нефть"}
    ]
},

{
    id:13,
    title:"Автоматизация контроля качества продукции",
    type:"article",
    annotation:"Разработка системы компьютерного зрения для промышленного контроля.",
    status:"published",
    access_level:"full",
    author_name:"Алексеева М.К.",
    created_at:"2025-01-25T14:00:00",
    tags:[
        {id:25,name:"computer vision"},
        {id:6,name:"AI"}
    ]
},

{
    id:14,
    title:"Исследование свойств новых катализаторов",
    type:"vkr",
    annotation:"Экспериментальное изучение эффективности химических катализаторов.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Морозов П.А.",
    created_at:"2025-04-22T11:00:00",
    tags:[
        {id:26,name:"химия"},
        {id:27,name:"катализаторы"}
    ]
},

{
    id:15,
    title:"Разработка REST API для научной платформы",
    type:"article",
    annotation:"Проектирование серверной архитектуры информационной системы.",
    status:"published",
    access_level:"full",
    author_name:"Васильев К.Н.",
    created_at:"2025-05-05T13:00:00",
    tags:[
        {id:12,name:"Backend"},
        {id:28,name:"API"}
    ]
},

{
    id:16,
    title:"Исследование возобновляемых источников энергии",
    type:"article",
    annotation:"Анализ перспектив использования солнечной и ветровой энергетики.",
    status:"published",
    access_level:"full",
    author_name:"Павлова Н.И.",
    created_at:"2024-10-10T10:00:00",
    tags:[
        {id:29,name:"энергетика"},
        {id:14,name:"экология"}
    ]
},

{
    id:17,
    title:"Прогнозирование отказов промышленного оборудования",
    type:"vkr",
    annotation:"Разработка модели предиктивного обслуживания оборудования.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Смирнов А.Д.",
    created_at:"2025-06-01T09:30:00",
    tags:[
        {id:30,name:"промышленность"},
        {id:7,name:"машинное обучение"}
    ]
},

{
    id:18,
    title:"Анализ больших данных в нефтегазовой отрасли",
    type:"article",
    annotation:"Методы обработки больших массивов производственной информации.",
    status:"published",
    access_level:"full",
    author_name:"Николаев В.В.",
    created_at:"2025-03-18T15:00:00",
    tags:[
        {id:10,name:"Big Data"},
        {id:2,name:"газ"}
    ]
},

{
    id:19,
    title:"Разработка системы управления лабораторными исследованиями",
    type:"vkr",
    annotation:"Создание информационной системы автоматизации лаборатории.",
    status:"moderation",
    access_level:"annotation_only",
    author_name:"Егорова Л.А.",
    created_at:"2025-06-20T12:00:00",
    tags:[
        {id:31,name:"информационные системы"},
        {id:28,name:"API"}
    ]
},

{
    id:20,
    title:"Исследование методов защиты промышленных сетей",
    type:"article",
    annotation:"Анализ современных подходов к информационной безопасности.",
    status:"published",
    access_level:"full",
    author_name:"Филиппов Р.С.",
    created_at:"2025-02-25T17:00:00",
    tags:[
        {id:32,name:"кибербезопасность"},
        {id:33,name:"сети"}
    ]
}

];