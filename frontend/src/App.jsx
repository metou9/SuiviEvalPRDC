import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PrimeReactProvider } from "primereact/api";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

import { AuthProvider } from "./auth/AuthProvider.jsx";
import { RequireAuth, RequireCapability } from "./auth/guards.jsx";

import AppShell from "./layout/AppShell.jsx";

import TechnicalExecution from "./pages/execution/TechnicalExecution.jsx";
import FinancialExecution from "./pages/execution/FinancialExecution.jsx";

import Archive from "./pages/Archive.jsx";
import Activities from "./pages/Activities.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Home from "./pages/Home.jsx";
import Indicators from "./pages/Indicators.jsx";
import Login from "./pages/Login.jsx";
import Measurements from "./pages/Measurements.jsx";
import Profile from "./pages/Profile.jsx";
import Reports from "./pages/Reports.jsx";

/* Infrastructure */
import Infrastructure from "./pages/infrastructure/Infrastructure.jsx";

import AdminIndicators from "./pages/admin/AdminIndicators.jsx";
import Geo from "./pages/admin/Geo.jsx";
import Program from "./pages/admin/Program.jsx";
import Reference from "./pages/admin/Reference.jsx";
import Users from "./pages/admin/Users.jsx";

import Budget from "./pages/finance/Budget.jsx";
import FinanceDashboard from "./pages/finance/FinanceDashboard.jsx";
import Transactions from "./pages/finance/Transactions.jsx";

import Ppm from "./pages/procurement/Ppm.jsx";
import ProcurementDashboard from "./pages/procurement/ProcurementDashboard.jsx";
import Processes from "./pages/procurement/Processes.jsx";


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});


export default function App() {
  return (
    <PrimeReactProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Routes>

              {/* =====================================================
                  LOGIN
              ===================================================== */}

              <Route path="/login" element={<Login />} />


              {/* =====================================================
                  APPLICATION AUTHENTIFIEE
              ===================================================== */}

              <Route
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              >

                {/* -------------------------------------------------
                    ACCUEIL
                ------------------------------------------------- */}

                <Route
                  path="/"
                  element={<Navigate to="/home" replace />}
                />

                <Route
                  path="/home"
                  element={<Home />}
                />

                <Route
                  path="/dashboard"
                  element={<Dashboard />}
                />


                {/* -------------------------------------------------
                    INDICATEURS
                ------------------------------------------------- */}

                <Route
                  path="/indicators"
                  element={<Indicators />}
                />

                <Route
                  path="/measurements"
                  element={<Measurements />}
                />


                {/* -------------------------------------------------
                    ACTIVITES
                ------------------------------------------------- */}

                <Route
                  path="/activities"
                  element={<Activities />}
                />


                {/* -------------------------------------------------
                    EXECUTION
                ------------------------------------------------- */}

                <Route
                  path="/execution/technical"
                  element={<TechnicalExecution />}
                />

                <Route
                  path="/execution/financial"
                  element={<FinancialExecution />}
                />


                {/* -------------------------------------------------
                    FINANCE
                ------------------------------------------------- */}

                <Route
                  path="/finance/budget"
                  element={<Budget />}
                />

                <Route
                  path="/finance/transactions"
                  element={<Transactions />}
                />

                <Route
                  path="/finance/dashboard"
                  element={<FinanceDashboard />}
                />


                {/* -------------------------------------------------
                    PASSATION DES MARCHES
                ------------------------------------------------- */}

                <Route
                  path="/procurement/ppm"
                  element={<Ppm />}
                />

                <Route
                  path="/procurement/processes"
                  element={<Processes />}
                />

                <Route
                  path="/procurement/dashboard"
                  element={<ProcurementDashboard />}
                />


                {/* -------------------------------------------------
                    INFRASTRUCTURE
                ------------------------------------------------- */}

                <Route
                  path="/execution/infrastructure"
                  element={<Infrastructure />}
                />


                {/* -------------------------------------------------
                    RAPPORTS
                ------------------------------------------------- */}

                <Route
                  path="/reports"
                  element={<Reports />}
                />


                {/* -------------------------------------------------
                    ARCHIVAGE
                ------------------------------------------------- */}

                <Route
                  path="/archive"
                  element={<Archive />}
                />


                {/* -------------------------------------------------
                    ADMINISTRATION / PARAMETRAGE
                ------------------------------------------------- */}

                <Route
                  path="/admin/geo"
                  element={
                    <RequireCapability cap="config.manage">
                      <Geo />
                    </RequireCapability>
                  }
                />

                <Route
                  path="/admin/program"
                  element={
                    <RequireCapability cap="config.manage">
                      <Program />
                    </RequireCapability>
                  }
                />

                <Route
                  path="/admin/indicators"
                  element={
                    <RequireCapability cap="config.manage">
                      <AdminIndicators />
                    </RequireCapability>
                  }
                />

                <Route
                  path="/admin/reference"
                  element={
                    <RequireCapability cap="config.manage">
                      <Reference />
                    </RequireCapability>
                  }
                />

                <Route
                  path="/admin/users"
                  element={
                    <RequireCapability cap="users.manage">
                      <Users />
                    </RequireCapability>
                  }
                />


                {/* -------------------------------------------------
                    PROFIL
                ------------------------------------------------- */}

                <Route
                  path="/profile"
                  element={<Profile />}
                />

              </Route>


              {/* =====================================================
                  ROUTE INCONNUE
              ===================================================== */}

              <Route
                path="*"
                element={<Navigate to="/home" replace />}
              />

            </Routes>
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </PrimeReactProvider>
  );
}