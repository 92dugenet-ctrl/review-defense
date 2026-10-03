import { createBrowserRouter, Navigate } from "react-router-dom";

import { RequireAuth } from "@/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { AdminPage } from "@/pages/AdminPage";
import { AnalysisPage } from "@/pages/AnalysisPage";
import { BillingPage } from "@/pages/BillingPage";
import { CaseDetailPage } from "@/pages/CaseDetailPage";
import { CasesPage } from "@/pages/CasesPage";
import { ContactPage } from "@/pages/ContactPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { HomePage } from "@/pages/HomePage";
import { LegalPage } from "@/pages/LegalPage";
import { LoginPage } from "@/pages/LoginPage";
import { MethodPage } from "@/pages/MethodPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { NotificationsPage } from "@/pages/NotificationsPage";
import { PricingPage } from "@/pages/PricingPage";
import { PrivacyPage } from "@/pages/PrivacyPage";
import { ProductPage } from "@/pages/ProductPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ReviewDetailPage } from "@/pages/ReviewDetailPage";
import { ReviewsPage } from "@/pages/ReviewsPage";
import { SecurityPage } from "@/pages/SecurityPage";
import { SettingsPage } from "@/pages/SettingsPage";

export const router = createBrowserRouter([
  // Public marketing pages.
  { path: "/", element: <HomePage /> },
  { path: "/produit", element: <ProductPage /> },
  { path: "/solutions", element: <Navigate to="/produit" replace /> },
  { path: "/fonctionnement", element: <MethodPage /> },
  { path: "/securite", element: <SecurityPage /> },
  { path: "/tarifs", element: <PricingPage /> },
  { path: "/ressources", element: <Navigate to="/fonctionnement" replace /> },
  { path: "/contact", element: <ContactPage /> },

  // Public legal information.
  { path: "/mentions-legales", element: <LegalPage /> },
  { path: "/confidentialite", element: <LegalPage /> },
  { path: "/cookies", element: <LegalPage /> },
  { path: "/cgu", element: <LegalPage /> },
  { path: "/cgv", element: <LegalPage /> },
  { path: "/accessibilite", element: <LegalPage /> },
  { path: "/contact-juridique", element: <LegalPage /> },

  // Authentication.
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },

  // Authenticated workspace. Organization-level authorization remains an API responsibility.
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/app",
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/app/dashboard" replace /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "reviews", element: <ReviewsPage /> },
          { path: "reviews/:id", element: <ReviewDetailPage /> },
          { path: "cases", element: <CasesPage /> },
          { path: "cases/:id", element: <CaseDetailPage /> },
          { path: "analysis", element: <AnalysisPage /> },
          { path: "notifications", element: <NotificationsPage /> },
          { path: "billing", element: <BillingPage /> },
          { path: "settings", element: <SettingsPage /> },
          { path: "privacy", element: <PrivacyPage /> },
          { path: "admin", element: <AdminPage /> },
        ],
      },
    ],
  },

  { path: "*", element: <NotFoundPage /> },
]);
