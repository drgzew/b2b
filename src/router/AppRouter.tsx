import { Routes, Route } from "react-router-dom";
import Login from "../pages/Login";
import Queue from "../pages/curator/Queue";
import ArtifactPage from "../pages/curator/ArtifactPage"
import RoleLayout from "../components/RoleLayout";

export default function AppRouter() {
    return (
        <Routes>
            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/curator/queue"
                element={
                    <RoleLayout>
                        <Queue />
                    </RoleLayout>
                }
            />

            <Route
                path="/curator/artifact/:id"
                element={
                    <RoleLayout>
                        <ArtifactPage />
                    </RoleLayout>
                }
            />

            {/* <Route
                path="/partner/dashboard"
                element={
                    <RoleLayout>
                        <Dashboard />
                    </RoleLayout>
                }
            /> */}
        </Routes>
    );
}