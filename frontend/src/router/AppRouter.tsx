import { Routes, Route, Navigate } from 'react-router-dom';
import Login from "../pages/Login";
import Queue from "../pages/curator/Queue";
import ArtifactPage from "../pages/curator/ArtifactPage";
import RoleLayout from "../components/RoleLayout";
// import Requests from "../pages/curator/Requests";
import MyArtifacts from "../pages/participant/MyArtifacts";
import PartnerDashboard from "../pages/partner/PartnerDashboard";
import PartnerDigest from "../pages/partner/PartnerDigest";
import PartnerInternships from '../pages/partner/PartnerInternships';
import PartnerFavorites from '../pages/partner/PartnerFavorites';
import CuratorRequests from '../pages/curator/CuratorRequests';

export default function AppRouter() {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />

            {/* Куратор */}
            <Route path="/curator/queue" element={<RoleLayout><Queue /></RoleLayout>} />
            <Route path="/curator/artifact/:id" element={<RoleLayout><ArtifactPage /></RoleLayout>} />
            {/* <Route path="/curator/requests" element={<RoleLayout><Requests /></RoleLayout>} /> */}
            <Route
                path="/curator/requests"
                element={<RoleLayout><CuratorRequests /></RoleLayout>}
            />
            {/* Участник */}
            <Route path="/participant/my-artifacts" element={<RoleLayout><MyArtifacts /></RoleLayout>} />

            {/* Партнёр */}
            <Route path="/partner/dashboard" element={<RoleLayout><PartnerDashboard /></RoleLayout>} />
            <Route path="/partner/digest" element={<RoleLayout><PartnerDigest /></RoleLayout>} />
            <Route path="/partner/digest/:topicId" element={<RoleLayout><PartnerDigest /></RoleLayout>} />
            <Route path="/partner/internships" element={<RoleLayout><PartnerInternships /></RoleLayout>} />
            <Route path="/partner/favorites" element={<RoleLayout><PartnerFavorites /></RoleLayout>} />
        </Routes>
    );
}



