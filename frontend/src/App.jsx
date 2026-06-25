import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/UploadPage';
import PipelinePage from './pages/PipelinePage';
import ICPConfigPage from './pages/ICPConfigPage';
import LeadDetailPage from './pages/LeadDetailPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/icp" element={<ICPConfigPage />} />
        <Route path="/leads/:id" element={<LeadDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
