import { useState } from "react";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { InputText } from "primereact/inputtext";
import { Password } from "primereact/password";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";

export default function Login() {
  const { t } = useTranslation();
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
      navigate("/dashboard");
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrap">
      <Card title={t("app.title")} style={{ width: "22rem" }}>
        <form onSubmit={submit} className="d-flex flex-column gap-3">
          <div>
            <label className="form-label">{t("auth.username")}</label>
            <InputText className="w-100" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </div>
          <div>
            <label className="form-label">{t("auth.password")}</label>
            <Password
              className="w-100"
              inputClassName="w-100"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              feedback={false}
              toggleMask
            />
          </div>
          {error && <small className="text-danger">{t("auth.error")}</small>}
          <Button type="submit" label={t("auth.signin")} loading={loading} />
        </form>
      </Card>
    </div>
  );
}
