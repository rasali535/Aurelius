import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import LandingPage from "./pages/LandingPage";
import "./styles.css";

function App() {
  const [inApp, setInApp] = useState(false);

  return inApp ? (
    <Dashboard />
  ) : (
    <LandingPage onEnterApp={() => setInApp(true)} />
  );
}

export default App;
