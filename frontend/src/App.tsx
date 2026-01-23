import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AcceptInvitePage from "./pages/AcceptInvitePage";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import DashboardPage from "./pages/DashboardPage";
import TasksPage from "./pages/TasksPage";
import FinancePage from "./pages/FinancePage";
import MeetingsPage from "./pages/MeetingsPage";
import FilesPage from "./pages/FilesPage";
import AIPage from "./pages/AIPage";
import ProfilePage from "./pages/ProfilePage";
import TeamPage from "./pages/TeamPage";
import LegalPage from "./pages/LegalPage";
import InvoicesPage from "./pages/InvoicesPage";
import AgingPage from "./pages/AgingPage";
import InventoryPage from "./pages/InventoryPage";
import NotificationsPage from "./pages/NotificationsPage";
import { AuthProvider } from "./context/AuthContext";



// Dashboard implementation imported from pages

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/accept-invite/:token" element={<AcceptInvitePage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/tasks" element={<TasksPage />} />
          <Route path="/dashboard/finance" element={<FinancePage />} />
          <Route path="/dashboard/invoices" element={<InvoicesPage />} />
          <Route path="/dashboard/aging" element={<AgingPage />} />
          <Route path="/dashboard/inventory" element={<InventoryPage />} />
          <Route path="/dashboard/notifications" element={<NotificationsPage />} />
          <Route path="/dashboard/meetings" element={<MeetingsPage />} />
          <Route path="/dashboard/team" element={<TeamPage />} />
          <Route path="/dashboard/files" element={<FilesPage />} />
          <Route path="/dashboard/ai" element={<AIPage />} />
          <Route path="/dashboard/legal" element={<LegalPage />} />
          <Route path="/dashboard/profile" element={<ProfilePage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
