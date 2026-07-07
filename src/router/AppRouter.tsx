import { Routes, Route } from "react-router-dom";
import Login from "../pages/Login";
import Queue from "../pages/curator/Queue";
import ArtifactPage from "../pages/curator/ArtifactPage"
import RoleLayout from "../components/RoleLayout";
import Requests from "../pages/curator/Requests";
import MyArtifacts from "../pages/participant/MyArtifacts";

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

            <Route
                path="/curator/requests"
                element={
                    <RoleLayout>
                        <Requests />
                    </RoleLayout>
                }
            />

            <Route
                path="/participant/my-artifacts"
                element={
                    <RoleLayout>
                        <MyArtifacts />
                    </RoleLayout>

                }
            />            
        </Routes>
    );
}