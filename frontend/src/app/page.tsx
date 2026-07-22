"use client";

import { useState } from "react";
import { Alert, Col, Container, Row } from "react-bootstrap";

import { AlertsTable } from "../components/alerts-table";
import { DashboardHeader } from "../components/dashboard-header";
import { FilesTable } from "../components/files-table";
import { UploadFileModal } from "../features/upload-file/upload-file-modal";
import { useFileDashboard } from "../hooks/use-file-dashboard";


export default function Page() {
  const [showModal, setShowModal] = useState(false);
  const dashboard = useFileDashboard();

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <DashboardHeader
            onRefresh={() => void dashboard.loadData()}
            onAddFile={() => setShowModal(true)}
          />
          {dashboard.errorMessage ? (
            <Alert variant="danger" className="shadow-sm">
              {dashboard.errorMessage}
            </Alert>
          ) : null}
          <FilesTable files={dashboard.files} isLoading={dashboard.isLoading} />
          <AlertsTable alerts={dashboard.alerts} isLoading={dashboard.isLoading} />
        </Col>
      </Row>
      <UploadFileModal
        show={showModal}
        isSubmitting={dashboard.isSubmitting}
        onClose={() => setShowModal(false)}
        onSubmit={dashboard.submitFile}
      />
    </Container>
  );
}
