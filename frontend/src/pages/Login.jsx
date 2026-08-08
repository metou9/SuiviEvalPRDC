import { useState } from "react";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
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
    <main className="login-wrap">
      <div className="login-overlay" />

      <Card className="login-card">
        <div className="login-header">
          <h1>Bienvenue</h1>

          <p>
            Connectez-vous pour accéder
            <br />
            à la plateforme de suivi-évaluation
            <br />
            du PRDC-VFS
          </p>
        </div>

        <form onSubmit={submit} className="login-form">
          <div className="login-field">
            <label htmlFor="username">Nom d’utilisateur</label>

            <InputText
              id="username"
              className="w-100"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
              disabled={loading}
              placeholder="Nom d’utilisateur"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Mot de passe</label>

            <Password
              id="password"
              className="w-100"
              inputClassName="w-100"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              feedback={false}
              toggleMask
              autoComplete="current-password"
              disabled={loading}
              placeholder="Mot de passe"
            />
          </div>

          {error && (
            <small className="login-error" role="alert">
              Identifiants invalides
            </small>
          )}

          <Button
            type="submit"
            label="Se connecter"
            loading={loading}
            disabled={loading || !username.trim() || !password}
            className="login-button"
          />
        </form>

        <footer className="login-footer">
          © 2026 Binor &amp; Associés / I&amp;D - Tous droits réservés
        </footer>
      </Card>
    </main>
  );
}