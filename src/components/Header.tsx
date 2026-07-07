import {useNavigate} from "react-router-dom";

interface HeaderItem {
    label:string;
    path:string;
}

interface HeaderProps {
    title?:string;
    menuItems?:HeaderItem[];
    role?:string;
}

export default function Header({
    title,
    menuItems = [],
    role
}:HeaderProps) {

    const navigate = useNavigate();

    return (
        <header className="header">
            <div className="header-left">
                <div className="logo-container">
                    <img
                        src="/utmn_logo.png"
                        alt="Логотип ТюмГУ"
                        className="logo-tmu"
                    />

                    <span className="logo-text">
                        Партнёрус
                    </span>

                </div>

                {
                    title && (
                        <>
                            <span className="divider">
                                |
                            </span>

                            <span className="cabinet-title">
                                {title}
                            </span>
                        </>
                    )
                }

            </div>

            {
                menuItems.length > 0 && (
                    <nav className="nav">

                        {
                            menuItems.map(item => (

                                <a
                                    key={item.path}
                                    onClick={() =>
                                        navigate(item.path)
                                    }
                                >
                                    {item.label}
                                </a>

                            ))
                        }

                        {
                            role && (
                                <span>
                                    {role}
                                </span>
                            )
                        }

                        <a
                            onClick={() =>
                                navigate("/login")
                            }
                        >
                            Выйти
                        </a>

                    </nav>
                )
            }
        </header>
    );
}