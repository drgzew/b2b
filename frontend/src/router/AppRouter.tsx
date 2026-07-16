import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../pages/Login';
import RoleLayout from '../components/RoleLayout';

import PartnerDashboard from '../pages/partner/PartnerDashboard';
import PartnerDigest from '../pages/partner/PartnerDigest';
import PartnerFavorites from '../pages/partner/PartnerFavorites';
import PartnerInternships from '../pages/partner/PartnerInternships';

import AuthorDashboard from '../pages/author/AuthorDashboard';
import AuthorRequests from '../pages/author/AuthorRequests';
import AuthorInternships from '../pages/author/AuthorInternships';
import AuthorLayout from '../layouts/AuthorLayout';

import AuthorProfile from '../pages/profile/AuthorProfile';
import TeacherProfile from '../pages/profile/TeacherProfile';

import Queue from '../pages/curator/Queue';
import ArtifactPage from '../pages/curator/ArtifactPage';
import MyArtifacts from '../pages/participant/MyArtifacts';
import AdminPanel from '../pages/admin/AdminPanel';
import CuratorRequests from '../pages/curator/CuratorRequests';

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />

      {/* Партнёр */}
      <Route path="/partner/dashboard" element={<RoleLayout><PartnerDashboard /></RoleLayout>} />
      <Route path="/partner/digest" element={<RoleLayout><PartnerDigest /></RoleLayout>} />
      <Route path="/partner/digest/:subscriptionId" element={<RoleLayout><PartnerDigest /></RoleLayout>} />
      <Route path="/partner/favorites" element={<RoleLayout><PartnerFavorites /></RoleLayout>} />
      <Route path="/partner/internships" element={<RoleLayout><PartnerInternships /></RoleLayout>} />

      {/* Автор */}
      <Route path="/author" element={<AuthorLayout />}>
        <Route path="dashboard" element={<AuthorDashboard />} />
        <Route path="requests" element={<AuthorRequests />} />
        <Route path="internships" element={<AuthorInternships />} />
      </Route>

      {/* Профили */}
      <Route path="/profile/author/:id" element={<RoleLayout><AuthorProfile /></RoleLayout>} />
      <Route path="/profile/teacher/:id" element={<RoleLayout><TeacherProfile /></RoleLayout>} />

      {/* Куратор */}
      <Route path="/curator/queue" element={<RoleLayout><Queue /></RoleLayout>} />
      <Route path="/curator/artifact/:id" element={<RoleLayout><ArtifactPage /></RoleLayout>} />
      <Route path="/curator/requests" element={<RoleLayout><CuratorRequests /></RoleLayout>} />

      {/* Участник (студент) */}
      <Route path="/participant/my-artifacts" element={<RoleLayout><MyArtifacts /></RoleLayout>} />

      {/* Админ */}
      <Route path="/admin" element={<RoleLayout><AdminPanel /></RoleLayout>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

export default AppRouter;