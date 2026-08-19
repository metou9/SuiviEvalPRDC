import { useState } from "react";
import { Button } from "primereact/button";
import { InputText } from "primereact/inputtext";
import { Password } from "primereact/password";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(false);
    setLoading(true);

    try {
      await login(username, password);
      navigate("/home");
    } catch (err) {
      console.error("Erreur de connexion :", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
  <main className="login-page">

    {/* ===================================================== */}
    {/* GAUCHE — CONNEXION */}
    {/* ===================================================== */}

    <section className="login-form-panel">
      <div className="login-form-container">


        <h2>Accéder à la plateforme</h2>

        <p className="login-form-intro">
          Identifiez-vous pour accéder à votre espace de suivi-évaluation.
        </p>

        <form onSubmit={submit} className="login-form">
          <div className="login-field">
            <label htmlFor="username">
              Nom d’utilisateur
            </label>

            <span className="login-input-container">
              <i className="pi pi-user" />

              <InputText
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                autoComplete="username"
                disabled={loading}
                placeholder="Saisissez votre nom d’utilisateur"
              />
            </span>
          </div>

          <div className="login-field">
            <label htmlFor="password">
              Mot de passe
            </label>

            <Password
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              feedback={false}
              toggleMask
              autoComplete="current-password"
              disabled={loading}
              placeholder="Saisissez votre mot de passe"
            />
          </div>

          {error && (
            <div className="login-error">
              <i className="pi pi-exclamation-circle" />
              Identifiants invalides
            </div>
          )}

          <Button
            type="submit"
            label="Se connecter"
            loading={loading}
            disabled={loading || !username.trim() || !password}
            className="login-submit"
          />
        </form>
      </div>
    </section>


    {/* ===================================================== */}
    {/* DROITE — PRÉSENTATION DU PROJET */}
    {/* ===================================================== */}

    <section className="login-project-panel">
      <div className="login-project-top">
        <div className="login-project-mark">
          <span>PR</span>
        </div>

        <div>
          <div className="login-project-code">
            PRDC-VFS
          </div>

          <div className="login-project-module">
            Suivi &amp; Évaluation
          </div>
        </div>
      </div>
<div className="login-project-logos">
  <div className="login-project-logo-card">
    <img
      src="/images/logo-mauritanie.svg"
      alt="République Islamique de Mauritanie"
    />
  </div>

  <div className="login-project-logo-card">
    <img
      src="/images/logo-prdc-vfs.png"
      alt="PRDC-VFS"
    />
  </div>

  <div className="login-project-logo-card login-project-logo-worldbank">
    <img
      src="/images/logo-worldbank.png"
      alt="Banque mondiale"
    />
  </div>
</div>
      <div className="login-project-content">
        <span className="login-project-eyebrow">
          PLATEFORME DE PILOTAGE
        </span>

        <h1>
          Plateforme de suivi-évaluation
          <br />
          du PRDC-VFS
        </h1>

        <p>
          Un espace centralisé pour la programmation, le suivi de
          l'exécution, le pilotage financier, le suivi des marchés
          et la mesure des résultats du projet.
        </p>

        <div className="login-project-features">
          <div>
            <i className="pi pi-calendar" />
            <span>Programmation</span>
          </div>

          <div>
            <i className="pi pi-chart-line" />
            <span>Suivi des résultats</span>
          </div>

          <div>
            <i className="pi pi-wallet" />
            <span>Pilotage financier</span>
          </div>
        </div>
      </div>

      <div className="login-project-footer">
        © 2026 <strong>Binor &amp; Associés</strong> — Tous droits réservés
      </div>
    </section>

  </main>
);
}